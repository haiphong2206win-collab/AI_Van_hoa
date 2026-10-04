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

from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["Models"])


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
    summary="[Placeholder] Lấy danh sách model AI được hỗ trợ",
    description="Endpoint tạm thời. Sẽ trả về HTTP 503 cho đến khi Người 7 hoàn thiện tích hợp ModelManager.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Chức năng đang chờ Người 7 tích hợp",
        }
    },
)
async def list_models() -> None:
    """Endpoint placeholder cho danh sách model.

    Người 7 sẽ thay thế hàm này để gọi ModelManager.list_models()
    khi hoàn thiện tầng AI.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "SERVICE_UNAVAILABLE",
            "message": "Chức năng đang chờ tích hợp.",
        },
    )
