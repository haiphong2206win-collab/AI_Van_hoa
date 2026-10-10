from typing import List, Literal, Tuple, get_args

from pydantic import BaseModel, ConfigDict, Field

ModelId = Literal["scratch", "finetuned"]
LoadState = Literal["unloaded", "loading", "ready", "error"]

MODEL_IDS: Tuple[str, ...] = get_args(ModelId)


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: ModelId = Field(..., examples=["scratch"])
    name: str = Field(..., min_length=1, examples=["Model tự xây"])
    available: bool
    load_state: LoadState


class ModelsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    models: List[ModelInfo]


# Tên cũ trong khung nền, giữ để code đã import không bị vỡ.
ModelItem = ModelInfo
ModelListResponse = ModelsResponse
