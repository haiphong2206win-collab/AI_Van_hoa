from typing import Any, Dict, Tuple

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., examples=["VALIDATION_ERROR"])
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


ERROR_CODES_BY_STATUS: Dict[int, Tuple[str, ...]] = {
    404: ("NOT_FOUND",),
    405: ("METHOD_NOT_ALLOWED",),
    413: ("IMAGE_TOO_LARGE",),
    415: ("INVALID_IMAGE",),
    422: ("VALIDATION_ERROR",),
    500: ("INFERENCE_FAILED", "INTERNAL_SERVER_ERROR"),
    503: ("MODEL_UNAVAILABLE", "SERVICE_UNAVAILABLE"),
    504: ("INFERENCE_TIMEOUT",),
}


def error_responses(*statuses: int) -> Dict[int, Dict[str, Any]]:
    """Dict cho `responses=` của route, ví dụ error_responses(413, 415, 422, 503, 504)."""
    return {
        status_code: {
            "model": ErrorResponse,
            "description": "Mã lỗi: " + " hoặc ".join(ERROR_CODES_BY_STATUS[status_code]),
        }
        for status_code in statuses
    }
