"""Lớp cơ sở trừu tượng cho Model AI Adapter (Base Model Interface).

Người phụ trách triển khai chính: Người 7.
Mục tiêu: Quy định hợp đồng chung cho mọi adapter model AI (scratch_model và finetuned_model).

Quy ước bắt buộc:
1. Giao diện đồng bộ (Synchronous):
   - load() -> None: Nạp trọng số từ artifact vào RAM/VRAM.
   - predict(image: PIL.Image.Image, question: str) -> str: Thực hiện tiền xử lý riêng, inference và giải mã kết quả.
   - unload() -> None: Giải phóng model và thu dọn bộ nhớ RAM/VRAM.
2. Quản lý bất đồng bộ (Async):
   - Các hàm này chạy đồng bộ (blocking CPU/GPU bound).
   - Người 7 có trách nhiệm chạy chúng ngoài FastAPI event loop (dùng asyncio.to_thread / run_in_executor).
3. Không import torch, transformers hay các thư viện AI nặng trong skeleton.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from enum import Enum
import time
from pydantic import BaseModel

if TYPE_CHECKING:
    import PIL.Image

class LoadState(str, Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"

class ModelInfo(BaseModel):
    id: str
    name: str
    available: bool
    load_state: LoadState

class BaseVIVQAModel(ABC):
    """Giao diện chuẩn cho các adapter mô hình VQA."""
    
    @abstractmethod
    def load(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def predict(self, image: Any, question: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        raise NotImplementedError

# --- MOCK MODEL DÙNG ĐỂ NGHIỆM THU ---
class MockVIVQAModel(BaseVIVQAModel):
    """Mô hình giả lập cố ý chạy chậm để test concurrency và timeout."""
    
    def __init__(self):
        self.state = LoadState.UNLOADED

    def load(self) -> None:
        self.state = LoadState.LOADING
        time.sleep(2)
        self.state = LoadState.READY

    def predict(self, image: Any, question: str) -> str:
        time.sleep(10)
        return f"Đây là câu trả lời giả lập. Câu hỏi nhận được: '{question}'"

    def unload(self) -> None:
        time.sleep(1)
        self.state = LoadState.UNLOADED