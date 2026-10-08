"""Endpoint danh sách model AI.

Người phụ trách triển khai chính: Người 7.
Khởi tạo khung / placeholder: Người 1 (Lead).

Hợp đồng dự kiến sau khi Người 7 tích hợp:
- Phương thức: GET /api/v1/models
- Trả về danh sách model (scratch, finetuned) kèm tên hiển thị, trạng thái available và load_state.

Trạng thái hiện tại:
- Placeholder trả về HTTP 503 SERVICE_UNAVAILABLE do chưa tích hợp ModelManager.
- Tuyệt đối không trả danh sách model với available=true giả lập.
"""

from fastapi import APIRouter, HTTPException, status, Request
from typing import List

from app.ai.base import ModelInfo

router = APIRouter(tags=["Models"])

@router.get(
    "/models",
    response_model=List[ModelInfo],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách model AI được hỗ trợ",
    description="Trả về metadata và trạng thái nạp (load_state) thực tế của model AI trên RAM.",
)
async def list_models(request: Request) -> List[ModelInfo]:
    manager = getattr(request.app.state, "model_manager", None)
    
    if manager is None or not manager._initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "ModelManager chưa được tích hợp hoặc đang khởi động.",
            },
        )
        
    return manager.list_models()