"""Điểm khởi chạy ứng dụng FastAPI chính (Application Entry Point).

Người phụ trách: Người 1 (Lead).
Mục tiêu:
- Khởi tạo FastAPI app thông qua hàm factory create_app().
- Thiết lập middleware CORS (allow_credentials=False, không wildcard).
- Đăng ký hệ thống xử lý lỗi tập trung.
- Gắn router tổng /api/v1.
- Quản lý vòng đời ứng dụng bằng lifespan.
- Đảm bảo backend khởi động trơn tru khi chưa có model weights.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.errors import register_error_handlers

settings = get_settings()

# Thiết lập logging cơ bản
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Quản lý vòng đời khởi động và tắt ứng dụng FastAPI.

    Ghi chú tích hợp cho Người 1 và Người 7:
    - Hiện tại chỉ ghi log trạng thái khởi động/tắt của phần nền.
    - TODO (Người 1): Khi Người 7 hoàn thiện và bàn giao app/ai/model_manager.py,
      tiến hành import model_manager và gọi:
          await model_manager.startup()
      ở khối khởi động.
    - TODO (Người 1): Tương tự, gọi:
          await model_manager.shutdown()
      ở khối dọn dẹp khi tắt ứng dụng.
    - Tuyệt đối không tự triển khai worker AI hoặc nuốt ngoại lệ tại đây.
    """
    logger.info("=== BẮT ĐẦU KHỞI ĐỘNG HỆ THỐNG: %s ===", settings.APP_NAME)
    logger.info("API Prefix: %s", settings.API_PREFIX)
    logger.info("CORS Allowed Origins: %s", settings.CORS_ORIGINS)
    logger.info("Chế độ thiết bị AI dự kiến: %s", settings.AI_DEVICE)
    logger.info("Thư mục Scratch Model: %s", settings.resolved_scratch_model_path)
    logger.info("Thư mục Finetuned Model: %s", settings.resolved_finetuned_model_path)
    logger.info("Lưu ý: Hệ thống đang ở pha nền tảng, chưa nạp trọng số model AI.")

    # Điểm chuyển giao quyền điều khiển cho ứng dụng
    yield

    logger.info("=== ĐANG TẮT HỆ THỐNG: %s ===", settings.APP_NAME)
    logger.info("Hoàn tất dọn dẹp tiến trình backend.")


def create_app() -> FastAPI:
    """Tạo và cấu hình ứng dụng FastAPI hoàn chỉnh."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Backend dịch vụ Hỏi Đáp Bằng Hình Ảnh (Image VQA Demo) "
            "hỗ trợ 2 model: scratch và finetuned."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Đăng ký Middleware CORS
    # Cho phép các origin đã cấu hình, cấm wildcard '*', allow_credentials=False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # 2. Đăng ký xử lý lỗi chung toàn hệ thống
    register_error_handlers(app)

    # 3. Đăng ký Router tổng hợp (chứa prefix /api/v1)
    app.include_router(api_router)

    return app


# Biến app instance cho ASGI servers (Uvicorn)
app = create_app()
