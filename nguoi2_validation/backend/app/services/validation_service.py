import unicodedata

from app.config import get_settings
from app.errors import AppError
from app.schemas.model import MODEL_IDS


def _validation_error(message: str) -> AppError:
    return AppError(code="VALIDATION_ERROR", message=message, status_code=422)


def validate_question(question: str) -> str:
    """Chuẩn hóa NFC, strip hai đầu, kiểm tra 1..MAX_QUESTION_LENGTH ký tự sau chuẩn hóa.

    Chuẩn hóa trước khi đếm để tiếng Việt dạng tổ hợp (NFD) không bị tính dài oan.
    """
    if not isinstance(question, str):
        raise _validation_error("Câu hỏi phải là chuỗi văn bản.")

    normalized = unicodedata.normalize("NFC", question).strip()
    if not normalized:
        raise _validation_error("Câu hỏi không được để trống.")

    max_length = get_settings().MAX_QUESTION_LENGTH
    if len(normalized) > max_length:
        raise _validation_error(f"Câu hỏi không được vượt quá {max_length} ký tự.")

    return normalized


def validate_model_id(model_id: str) -> str:
    """Chỉ nhận đúng id trong MODEL_IDS; không sửa id sai và không in lại giá trị người dùng gửi."""
    if not isinstance(model_id, str) or model_id not in MODEL_IDS:
        raise _validation_error("model_id không hợp lệ. Chỉ chấp nhận: " + ", ".join(MODEL_IDS) + ".")
    return model_id
