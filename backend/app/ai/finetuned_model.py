"""Adapter cho Model Fine-tuned (Finetuned Model Adapter).

Người phụ trách triển khai chính: Người 6.
Mục tiêu: Đóng gói logic nạp trọng số, tiền xử lý và suy luận của Finetuned Model
vào lớp FinetunedVIVQAModel tuân thủ BaseVIVQAModel.

Hợp đồng giao diện (Synchronous):
- load() -> None: Đọc trọng số từ Settings.resolved_finetuned_model_path.
- predict(image: PIL.Image.Image, question: str) -> str: Thực hiện processor/tokenizer và forward pass.
- unload() -> None: Xóa model khỏi bộ nhớ, dọn dẹp cache GPU/RAM.

Lưu ý:
- Không import torch/transformers trong bước khung nền này.
- Người 6 sẽ đề xuất bổ sung thư viện tương ứng vào requirements.txt sau khi chốt artifact.
- Tuyệt đối không sinh câu trả lời giả mô phỏng.
"""

from typing import TYPE_CHECKING, Any
from app.ai.base import BaseVIVQAModel
from app.config import get_settings

if TYPE_CHECKING:
    import PIL.Image

settings = get_settings()


class FinetunedVIVQAModel(BaseVIVQAModel):
    """Lớp điều phối adapter cho model fine-tuned."""

    def __init__(self) -> None:
        self.model_path = settings.resolved_finetuned_model_path
        self.device = settings.AI_DEVICE
        self._is_loaded = False

    def load(self) -> None:
        """Nạp trọng số finetuned model.

        TODO (Người 6 triển khai):
        - Kiểm tra sự tồn tại của artifact tại self.model_path.
        - Khởi tạo kiến trúc pretrained + fine-tuned head.
        - Nạp weights và chuyển sang self.device.
        - Đặt self._is_loaded = True.
        """
        raise NotImplementedError("FinetunedVIVQAModel.load đang chờ Người 6 triển khai.")

    def predict(self, image: Any, question: str) -> str:
        """Thực hiện suy luận VQA với finetuned model.

        TODO (Người 6 triển khai):
        - Tiền xử lý ảnh theo quy chuẩn của model pretrained.
        - Tokenize câu hỏi đầu vào.
        - Chạy generate/inference và decode chuỗi câu trả lời.
        """
        raise NotImplementedError("FinetunedVIVQAModel.predict đang chờ Người 6 triển khai.")

    def unload(self) -> None:
        """Giải phóng finetuned model khỏi bộ nhớ.

        TODO (Người 6 triển khai):
        - Xóa tham chiếu model, giải phóng VRAM (nếu dùng CUDA).
        - Đặt self._is_loaded = False.
        """
        raise NotImplementedError("FinetunedVIVQAModel.unload đang chờ Người 6 triển khai.")
