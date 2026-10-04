"""Dịch vụ kiểm tra và xác thực nghiệp vụ (Validation Service).

Người phụ trách triển khai chính: Người 2.
Mục tiêu: Cung cấp các hàm kiểm tra tính hợp lệ của câu hỏi và model_id theo ràng buộc dự án.

Hợp đồng giao diện dự kiến:
- validate_question(question: str) -> str:
    + Loại bỏ khoảng trắng thừa (strip).
    + Kiểm tra độ dài từ 1 đến 2000 ký tự (lấy cấu hình từ Settings.MAX_QUESTION_LENGTH).
    + Ném lỗi AppError hoặc ValueError nếu không hợp lệ.
    + Trả về chuỗi câu hỏi đã được làm sạch.
- validate_model_id(model_id: str) -> str:
    + Kiểm tra model_id phải thuộc tập hợp cho phép: {'scratch', 'finetuned'}.
    + Ném lỗi nếu model_id không hợp lệ.
    + Trả về model_id hợp lệ.

Trạng thái hiện tại:
- Skeleton dùng NotImplementedError thay vì trả dữ liệu giả.
"""

from app.config import get_settings

settings = get_settings()


def validate_question(question: str) -> str:
    """Xác thực và chuẩn hóa câu hỏi người dùng nhập.

    TODO (Người 2 triển khai):
    - Trim khoảng trắng đầu/cuối.
    - Kiểm tra chuỗi không rỗng.
    - Kiểm tra độ dài <= settings.MAX_QUESTION_LENGTH.
    - Trả về câu hỏi sau khi chuẩn hóa.
    """
    raise NotImplementedError("validate_question đang chờ Người 2 triển khai.")


def validate_model_id(model_id: str) -> str:
    """Xác thực mã model được chọn.

    TODO (Người 2 triển khai):
    - Kiểm tra model_id nằm trong ('scratch', 'finetuned').
    - Trả về model_id hợp lệ.
    """
    raise NotImplementedError("validate_model_id đang chờ Người 2 triển khai.")
