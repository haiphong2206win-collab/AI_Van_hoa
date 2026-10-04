"""Adapter cho Model huấn luyện từ đầu (Scratch Model Adapter).

Người phụ trách triển khai chính: Người 5.
Mục tiêu: Đóng gói logic nạp trọng số, tiền xử lý và suy luận của Scratch Model
vào lớp ScratchVIVQAModel tuân thủ BaseVIVQAModel.

Hợp đồng giao diện (Synchronous):
- load() -> None: Đọc trọng số từ Settings.resolved_scratch_model_path.
- predict(image: PIL.Image.Image, question: str) -> str: Thực hiện tokenizer/feature extractor và forward pass.
- unload() -> None: Xóa model khỏi bộ nhớ, dọn dẹp cache GPU/RAM.

Lưu ý:
- Không import torch/transformers trong bước khung nền này.
- Người 5 sẽ đề xuất bổ sung torch/transformers/torchvision vào requirements.txt sau khi chốt artifact.
- Tuyệt đối không sinh câu trả lời giả mô phỏng.
"""

from typing import TYPE_CHECKING, Any
from app.ai.base import BaseVIVQAModel
from app.config import get_settings

if TYPE_CHECKING:
    import PIL.Image

settings = get_settings()


class ScratchVIVQAModel(BaseVIVQAModel):
    """Lớp điều phối adapter cho model scratch."""

    def __init__(self) -> None:
        self.model_path = settings.resolved_scratch_model_path
        self.device = settings.AI_DEVICE
        self._is_loaded = False

    def load(self) -> None:
        """Nạp trọng số scratch model.

        TODO (Người 5 triển khai):
        - Kiểm tra sự tồn tại của artifact tại self.model_path.
        - Khởi tạo kiến trúc model và nạp state_dict hoặc pipeline.
        - Đặt self._is_loaded = True.
        """
        raise NotImplementedError("ScratchVIVQAModel.load đang chờ Người 5 triển khai.")

    def predict(self, image: Any, question: str) -> str:
        """Thực hiện suy luận VQA với scratch model.

        TODO (Người 5 triển khai):
        - Tiền xử lý ảnh và tokenize câu hỏi.
        - Thực hiện forward pass trên self.device.
        - Giải mã tensor đầu ra thành chuỗi câu trả lời tiếng Việt.
        """
        raise NotImplementedError("ScratchVIVQAModel.predict đang chờ Người 5 triển khai.")

    def unload(self) -> None:
        """Giải phóng scratch model khỏi bộ nhớ.

        TODO (Người 5 triển khai):
        - Xóa tham chiếu model, giải phóng VRAM (nếu dùng CUDA).
        - Đặt self._is_loaded = False.
        """
        raise NotImplementedError("ScratchVIVQAModel.unload đang chờ Người 5 triển khai.")
