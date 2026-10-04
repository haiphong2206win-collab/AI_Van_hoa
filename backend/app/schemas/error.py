"""Pydantic schemas cho phản hồi lỗi chuẩn (Error Response).

Người phụ trách triển khai chính: Người 2.
Mục tiêu: Mô hình hóa định dạng lỗi JSON thống nhất toàn hệ thống:
    {"error": {"code": "VALIDATION_ERROR", "message": "Thông tin lỗi dễ hiểu."}}
"""

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Chi tiết mã lỗi và thông điệp lỗi gửi tới frontend."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        description="Mã lỗi dạng SNAKE_CASE (VD: VALIDATION_ERROR, SERVICE_UNAVAILABLE)",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Thông báo lỗi thân thiện, dễ hiểu cho người dùng cuối",
        examples=["Câu hỏi không được để trống hoặc vượt quá 2000 ký tự."],
    )


class ErrorResponse(BaseModel):
    """Bao bọc phản hồi lỗi chuẩn của toàn bộ API."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail = Field(..., description="Đối tượng chứa thông tin lỗi")
