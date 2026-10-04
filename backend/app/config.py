"""Cấu hình ứng dụng Backend.

Người phụ trách: Người 1 (Lead).
Mục tiêu: Đọc biến môi trường và file .env qua pydantic-settings, chuẩn hóa đường dẫn,
kiểm tra tính hợp lệ của cấu hình trước khi ứng dụng khởi chạy.
"""

from functools import lru_cache
import json
from pathlib import Path
from typing import Any, List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Đường dẫn gốc của backend (thư mục chứa app/, model_artifacts/, .env)
BACKEND_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Cấu hình toàn hệ thống backend."""

    # Tên ứng dụng
    APP_NAME: str = Field(default="Image VQA Demo", description="Tên ứng dụng")
    
    # Prefix cho toàn bộ API (chỉ đặt một lần ở router tổng)
    API_PREFIX: str = Field(default="/api/v1", description="Prefix chung của API")
    
    # Cấu hình Host và Port để phục vụ việc chạy server
    # Lưu ý: Uvicorn CLI không tự động đọc HOST/PORT từ .env nếu không truyền tham số.
    HOST: str = Field(default="127.0.0.1", description="Host lắng nghe")
    PORT: int = Field(default=8000, description="Cổng lắng nghe")
    
    # Cấu hình CORS - Nhận JSON array từ .env
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        description="Danh sách origin được phép truy cập CORS",
    )
    
    # Đường dẫn thư mục chứa trọng số model (tương đối từ BACKEND_ROOT hoặc tuyệt đối)
    SCRATCH_MODEL_PATH: str = Field(
        default="model_artifacts/scratch",
        description="Đường dẫn thư mục trọng số scratch model",
    )
    FINETUNED_MODEL_PATH: str = Field(
        default="model_artifacts/finetuned",
        description="Đường dẫn thư mục trọng số finetuned model",
    )
    
    # Thiết bị chạy suy luận AI (cpu / cuda)
    AI_DEVICE: str = Field(default="cpu", description="Thiết bị AI dự kiến")
    
    # Giới hạn kích thước file upload (mặc định 10 MiB = 10 * 1024 * 1024 bytes)
    MAX_UPLOAD_BYTES: int = Field(default=10485760, description="Dung lượng upload tối đa (bytes)")
    
    # Giới hạn độ dài câu hỏi
    MAX_QUESTION_LENGTH: int = Field(default=2000, description="Độ dài câu hỏi tối đa (ký tự)")
    
    # Thời gian timeout suy luận (giây)
    INFERENCE_TIMEOUT_SECONDS: int = Field(
        default=180, description="Thời gian timeout suy luận tối đa (giây)"
    )
    
    # Cấp độ log
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str], Any]) -> List[str]:
        """Parse và kiểm tra CORS origins, không cho phép ký tự đại diện wildcard '*'."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        value = parsed
                except json.JSONDecodeError as exc:
                    raise ValueError(f"CORS_ORIGINS không phải JSON array hợp lệ: {exc}") from exc
            else:
                # Trường hợp chuỗi phân cách bởi dấu phẩy
                value = [item.strip() for item in value.split(",") if item.strip()]

        if not isinstance(value, list):
            raise ValueError("CORS_ORIGINS phải là danh sách các URL origins.")

        origins = [str(orig).strip().rstrip("/") for orig in value if str(orig).strip()]
        for origin in origins:
            if origin == "*":
                raise ValueError(
                    "Cấm sử dụng wildcard '*' trong CORS_ORIGINS vì lý do an toàn bảo mật."
                )
        return origins

    @field_validator("MAX_UPLOAD_BYTES")
    @classmethod
    def validate_max_upload(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("MAX_UPLOAD_BYTES phải là số nguyên dương (> 0).")
        return value

    @field_validator("MAX_QUESTION_LENGTH")
    @classmethod
    def validate_max_question_length(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("MAX_QUESTION_LENGTH phải là số nguyên dương (> 0).")
        return value

    @field_validator("INFERENCE_TIMEOUT_SECONDS")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("INFERENCE_TIMEOUT_SECONDS phải là số nguyên dương (> 0).")
        return value

    @field_validator("PORT")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not (1 <= value <= 65535):
            raise ValueError("PORT phải nằm trong khoảng từ 1 đến 65535.")
        return value

    @field_validator("API_PREFIX")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        prefix = value.strip()
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        if len(prefix) > 1 and prefix.endswith("/"):
            prefix = prefix.rstrip("/")
        return prefix

    @property
    def resolved_scratch_model_path(self) -> Path:
        """Đường dẫn thư mục scratch model được resolve từ BACKEND_ROOT."""
        p = Path(self.SCRATCH_MODEL_PATH)
        return p if p.is_absolute() else (BACKEND_ROOT / p).resolve()

    @property
    def resolved_finetuned_model_path(self) -> Path:
        """Đường dẫn thư mục finetuned model được resolve từ BACKEND_ROOT."""
        p = Path(self.FINETUNED_MODEL_PATH)
        return p if p.is_absolute() else (BACKEND_ROOT / p).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Trả về instance cấu hình singleton được cache."""
    return Settings()
