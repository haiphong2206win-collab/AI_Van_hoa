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

if TYPE_CHECKING:
    import PIL.Image


class BaseVIVQAModel(ABC):
    """Giao diện chuẩn cho các adapter mô hình VQA."""

    @abstractmethod
    def load(self) -> None:
        """Nạp trọng số và khởi tạo pipeline mô hình."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, image: Any, question: str) -> str:
        """Thực hiện suy luận trả lời câu hỏi dựa trên hình ảnh."""
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        """Giải phóng mô hình khỏi bộ nhớ."""
        raise NotImplementedError
