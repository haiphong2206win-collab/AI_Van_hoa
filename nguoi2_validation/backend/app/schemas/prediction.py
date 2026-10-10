from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.model import ModelId


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: ModelId = Field(..., examples=["scratch"])
    question: str = Field(..., min_length=1, description="Câu hỏi đã chuẩn hóa", examples=["Đây là địa danh nào?"])
    answer: str = Field(..., min_length=1, examples=["Chùa Một Cột tại Hà Nội."])

    @field_validator("answer")
    @classmethod
    def answer_must_have_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("answer không được rỗng.")
        return value
