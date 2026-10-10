import unicodedata
import unittest

from pydantic import ValidationError

from app.errors import AppError, format_error_payload
from app.schemas.error import ErrorResponse, error_responses
from app.schemas.model import MODEL_IDS, ModelsResponse
from app.schemas.prediction import PredictionResponse
from app.services.validation_service import validate_model_id, validate_question


def _error_of(func, value) -> AppError:
    with_error = None
    try:
        func(value)
    except AppError as exc:
        with_error = exc
    assert with_error is not None, f"{func.__name__}({value!r}) lẽ ra phải ném AppError"
    return with_error


class ValidateQuestionTest(unittest.TestCase):
    def test_empty_and_whitespace_only_rejected(self) -> None:
        for value in ["", " ", "   ", "\n", "\t \r\n", "\u00a0", "\u3000"]:
            with self.subTest(value=value):
                exc = _error_of(validate_question, value)
                self.assertEqual((exc.status_code, exc.code), (422, "VALIDATION_ERROR"))
                self.assertEqual(exc.message, "Câu hỏi không được để trống.")

    def test_strip_keeps_inner_content_case_and_newlines(self) -> None:
        self.assertEqual(validate_question("  Ảnh này là GÌ?  "), "Ảnh này là GÌ?")
        self.assertEqual(validate_question("\n dòng 1\n\ndòng  2 \t"), "dòng 1\n\ndòng  2")

    def test_vietnamese_unicode_normalized_to_nfc(self) -> None:
        nfc = "Đây là áo dài truyền thống ở Việt Nam?"
        nfd = unicodedata.normalize("NFD", nfc)
        self.assertNotEqual(nfc, nfd)
        self.assertEqual(validate_question(nfd), nfc)
        self.assertEqual(validate_question(nfc), nfc)

    def test_length_boundary_2000_and_2001(self) -> None:
        self.assertEqual(len(validate_question("a" * 2000)), 2000)
        exc = _error_of(validate_question, "a" * 2001)
        self.assertEqual((exc.status_code, exc.code), (422, "VALIDATION_ERROR"))
        self.assertEqual(exc.message, "Câu hỏi không được vượt quá 2000 ký tự.")

    def test_length_counted_after_strip_and_nfc(self) -> None:
        self.assertEqual(len(validate_question("  " + "a" * 2000 + "\n")), 2000)
        # 2000 chữ "ế" dạng NFD là 6000 ký tự thô nhưng 2000 sau NFC -> hợp lệ.
        raw = unicodedata.normalize("NFD", "ế" * 2000)
        self.assertGreater(len(raw), 2000)
        self.assertEqual(validate_question(raw), "ế" * 2000)
        _error_of(validate_question, "ế" * 2001)

    def test_non_string_rejected(self) -> None:
        for value in [None, 123, b"abc", ["a"]]:
            with self.subTest(value=value):
                self.assertEqual(_error_of(validate_question, value).code, "VALIDATION_ERROR")


class ValidateModelIdTest(unittest.TestCase):
    def test_valid_ids_returned_unchanged(self) -> None:
        for value in ["scratch", "finetuned"]:
            self.assertEqual(validate_model_id(value), value)
        self.assertEqual(MODEL_IDS, ("scratch", "finetuned"))

    def test_unknown_ids_rejected_without_auto_fix(self) -> None:
        for value in ["", " ", "scratch ", " scratch", "Scratch", "FINETUNED", "fine-tune", "other", "scratch\n"]:
            with self.subTest(value=value):
                exc = _error_of(validate_model_id, value)
                self.assertEqual((exc.status_code, exc.code), (422, "VALIDATION_ERROR"))
                self.assertEqual(exc.message, "model_id không hợp lệ. Chỉ chấp nhận: scratch, finetuned.")

    def test_message_does_not_echo_user_input(self) -> None:
        self.assertNotIn("<script>", _error_of(validate_model_id, "<script>").message)

    def test_non_string_rejected(self) -> None:
        self.assertEqual(_error_of(validate_model_id, None).code, "VALIDATION_ERROR")


class ErrorFormatTest(unittest.TestCase):
    def test_app_error_payload_matches_error_response_schema(self) -> None:
        exc = _error_of(validate_question, "")
        payload = format_error_payload(exc.code, exc.message)
        self.assertEqual(ErrorResponse.model_validate(payload).model_dump(), payload)
        self.assertEqual(list(payload), ["error"])
        self.assertEqual(list(payload["error"]), ["code", "message"])

    def test_error_response_forbids_extra_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ErrorResponse.model_validate({"error": {"code": "X", "message": "y", "detail": "z"}})

    def test_error_responses_helper_for_openapi(self) -> None:
        docs = error_responses(413, 415, 422, 500, 503, 504)
        self.assertEqual(sorted(docs), [413, 415, 422, 500, 503, 504])
        self.assertIs(docs[422]["model"], ErrorResponse)
        self.assertIn("MODEL_UNAVAILABLE", docs[503]["description"])
        self.assertIn("INFERENCE_FAILED", docs[500]["description"])


class ResponseSchemaTest(unittest.TestCase):
    def test_prediction_response_unicode_and_exact_keys(self) -> None:
        body = PredictionResponse(model_id="scratch", question="Trong ảnh có gì?", answer="Chùa Một Cột tại Hà Nội.")
        self.assertEqual(set(body.model_dump()), {"model_id", "question", "answer"})
        self.assertEqual(body.answer, "Chùa Một Cột tại Hà Nội.")

    def test_prediction_response_rejects_blank_answer_unknown_model_and_extra(self) -> None:
        base = {"model_id": "scratch", "question": "q", "answer": "a"}
        for patch in [{"answer": ""}, {"answer": "  \n"}, {"model_id": "other"}, {"question": ""}, {"confidence": 0.9}]:
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                PredictionResponse.model_validate({**base, **patch})

    def test_models_response_matches_contract_example(self) -> None:
        example = {
            "models": [
                {"id": "scratch", "name": "Model tự xây", "available": True, "load_state": "unloaded"},
                {"id": "finetuned", "name": "Model fine tune", "available": False, "load_state": "error"},
            ]
        }
        self.assertEqual(ModelsResponse.model_validate(example).model_dump(), example)

    def test_models_response_rejects_unknown_id_or_state(self) -> None:
        item = {"id": "scratch", "name": "n", "available": True, "load_state": "ready"}
        for patch in [{"id": "other"}, {"load_state": "busy"}, {"extra": 1}]:
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ModelsResponse.model_validate({"models": [{**item, **patch}]})


if __name__ == "__main__":
    unittest.main()
