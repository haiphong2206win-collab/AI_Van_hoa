"""Endpoint suy luận hỏi đáp bằng ảnh (VQA Predict).

Người phụ trách triển khai chính: Người 4.
Khởi tạo khung / placeholder: Người 1 (Lead).

Hợp đồng dự kiến sau khi hoàn thiện:
- Phương thức: POST /api/v1/predict
- Body: multipart/form-data gồm file (ảnh), question (chuỗi), model_id ('scratch' | 'finetuned').
- Trả về: {"model_id": "...", "question": "...", "answer": "..."}

Trạng thái hiện tại:
- Placeholder kiểm tra sự hiện diện của các trường bắt buộc thông qua FastAPI Form/File.
- Không đọc, không lưu nội dung ảnh vào bộ nhớ hay đĩa.
- Luôn đóng stream của UploadFile an toàn trong khối finally.
- Trả về HTTP 503 SERVICE_UNAVAILABLE do chưa tích hợp tầng AI và ImageService.
- Tuyệt đối không sinh câu trả lời giả để mô phỏng.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

router = APIRouter(tags=["Predict"])


@router.post(
    "/predict",
    status_code=status.HTTP_200_OK,
    summary="[Placeholder] Gửi ảnh và câu hỏi để suy luận VQA",
    description=(
        "Endpoint tạm thời. Nhận multipart/form-data gồm file, question, model_id. "
        "Hiện tại trả về HTTP 503 cho đến khi Người 4 hoàn tất tích hợp cùng Người 2, 3, 7."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Chức năng đang chờ tích hợp",
        },
        422: {
            "description": "Thiếu các trường bắt buộc (file, question, model_id)",
        },

    },
)
async def predict_placeholder(
    file: UploadFile = File(..., description="File ảnh câu hỏi"),
    question: str = Form(..., description="Nội dung câu hỏi"),
    model_id: str = Form(..., description="Mã model được chọn: 'scratch' hoặc 'finetuned'"),
) -> None:
    """Endpoint placeholder nhận input multipart/form-data và trả về 503."""
    try:
        # Không đọc bytes hay lưu file ảnh tại bước placeholder
        pass
    finally:
        # Đảm bảo đóng file upload để giải phóng tài nguyên tạm của OS
        await file.close()

    # Ném lỗi 503 thông báo chưa tích hợp dịch vụ AI
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "SERVICE_UNAVAILABLE",
            "message": "Chức năng đang chờ tích hợp.",
        },
    )
