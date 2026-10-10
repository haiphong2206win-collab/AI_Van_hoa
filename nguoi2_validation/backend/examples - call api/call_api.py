"""Ví dụ gọi API VQA bằng Python (thư viện requests: pip install requests).

Chạy:  python examples/call_api.py anh.jpg "Trong ảnh có gì?" scratch
Hàm ask_ai / list_models dùng được trực tiếp trong script hoặc giao diện Python (Tkinter, Streamlit...).
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

API = "http://127.0.0.1:8000/api/v1"
# Dài hơn deadline 180 giây của backend để nhận được 504 có JSON thay vì tự cắt trước.
TIMEOUT_SECONDS = 200


class ApiError(Exception):
    """Lỗi từ backend (có status/code) hoặc lỗi kết nối (status=None)."""

    def __init__(self, message: str, status: Optional[int] = None, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def _error_from(response: requests.Response) -> ApiError:
    try:
        error = response.json()["error"]
        return ApiError(error["message"], response.status_code, error.get("code"))
    except (ValueError, KeyError, TypeError):
        return ApiError(f"Yêu cầu thất bại ({response.status_code})", response.status_code)


def list_models() -> List[Dict[str, Any]]:
    """GET /models -> [{"id", "name", "available", "load_state"}, ...]."""
    try:
        response = requests.get(f"{API}/models", timeout=10)
    except requests.RequestException as exc:
        raise ApiError(f"Không kết nối được backend: {exc.__class__.__name__}") from exc
    if not response.ok:
        raise _error_from(response)
    return response.json()["models"]


def ask_ai(image_path: str, question: str, model_id: str) -> Dict[str, str]:
    """POST /predict -> {"model_id", "question" (đã chuẩn hóa), "answer"}.

    Không tự gửi lại khi timeout hoặc lỗi mạng: tác vụ trước có thể vẫn đang chạy ở backend.
    requests tự tạo Content-Type multipart kèm boundary, không đặt header này thủ công.
    """
    path = Path(image_path)
    with path.open("rb") as image_file:
        try:
            response = requests.post(
                f"{API}/predict",
                files={"file": (path.name, image_file)},
                data={"question": question, "model_id": model_id},
                timeout=TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise ApiError(f"Không kết nối được backend: {exc.__class__.__name__}") from exc

    if not response.ok:
        raise _error_from(response)

    body = response.json()
    answer = body.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ApiError("Phản hồi AI không hợp lệ", response.status_code)
    return body


def main(argv: List[str]) -> int:
    if len(argv) != 4:
        print('Cách dùng: python examples/call_api.py <ảnh> "<câu hỏi>" <scratch|finetuned>')
        return 2
    try:
        result = ask_ai(argv[1], argv[2], argv[3])
    except ApiError as exc:
        print(f"Lỗi [{exc.status} {exc.code}]: {exc}")
        return 1
    print(f"Câu hỏi: {result['question']}\nTrả lời ({result['model_id']}): {result['answer']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))