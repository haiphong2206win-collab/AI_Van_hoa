"""Pydantic schemas cho API danh sách model AI.

Người phụ trách triển khai chính: Người 2.
Mục tiêu: Định nghĩa schema cấu trúc thông tin model trả về cho client.

Hợp đồng dữ liệu thống nhất:
- GET /api/v1/models
- Response HTTP 200 dự kiến:
    {
        "models": [
            {
                "id": "scratch",
                "name": "Model tự xây",
                "available": false,
                "load_state": "unloaded"
            },
            ...
        ]
    }
- load_state: unloaded | loading | ready | error
"""

from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field


# TODO (Người 2): Hoàn thiện và cập nhật schema theo thực tế khi Người 7 bàn giao ModelManager
class ModelItem(BaseModel):
    """Thông tin chi tiết của từng model AI."""

    model_config = ConfigDict(extra="forbid")

    id: Literal["scratch", "finetuned"] = Field(..., description="Mã định danh duy nhất của model")
    name: str = Field(..., description="Tên hiển thị thân thiện với người dùng")
    available: bool = Field(
        ...,
        description="Model có sẵn sàng phục vụ suy luận hay không",
    )
    load_state: Literal["unloaded", "loading", "ready", "error"] = Field(
        ...,
        description="Trạng thái nạp trọng số hiện tại của model",
    )


class ModelListResponse(BaseModel):
    """Danh sách các model AI được backend hỗ trợ."""

    model_config = ConfigDict(extra="forbid")

    models: List[ModelItem] = Field(..., description="Danh sách model hỗ trợ")
