"""Bộ quản lý và điều phối các Model AI (Model Manager).

Người phụ trách triển khai chính: Người 7.
Mục tiêu: Quản lý vòng đời (startup, shutdown), caching/tái sử dụng model đã nạp,
và tuần tự hóa (serialization/concurrency control) các lượt suy luận AI.

Giao diện quản lý dự kiến (Async):
- async def startup() -> None
- async def predict(model_id: str, image: "PIL.Image.Image", question: str) -> str
- def list_models() -> list
- async def shutdown() -> None

Quy ước cốt lõi bắt buộc khi tích hợp (Tránh lỗi tranh chấp tài nguyên và crash server):
1. Đơn tiến trình & Đơn lượt chạy (Single Process & Single Inference):
   - Một backend process chỉ chạy duy nhất MỘT lượt suy luận AI tại một thời điểm (dùng asyncio.Lock).
2. Tái sử dụng model:
   - Giữ model đã nạp trong bộ nhớ nếu các request tiếp theo dùng cùng model_id.
   - Chỉ dỡ bỏ (unload) và nạp (load) model khác khi client yêu cầu chuyển model_id.
3. Cơ chế điều phối đồng nhất:
   - Các thao tác: Nạp (load), Đổi (switch), Giải phóng (unload) và Suy luận (predict)
     PHẢI dùng chung một khóa điều phối (Lock) để tránh race conditions.
4. Trách nhiệm xử lý Timeout và Ngắt kết nối:
   - Timeout HTTP (Settings.INFERENCE_TIMEOUT_SECONDS) hoặc việc Client ngắt kết nối
     KHÔNG ĐỒNG NGHĨA với việc thread/model AI bên dưới đã dừng ngay lập tức.
   - Nếu AI đang chạy trong thread worker, PHẢI giữ tài nguyên ảnh và khóa điều phối
     cho đến khi lượt suy luận đó kết thúc hoàn toàn. KHÔNG được đóng ảnh hoặc nạp/chạy
     model khác đè lên khi lượt trước chưa giải phóng tài nguyên.
   - Yêu cầu xếp hàng chờ trong queue nếu đã quá thời gian timeout trước khi bắt đầu
     thì PHẢI bị hủy bỏ (discard/skip), tuyệt đối không để chạy ngầm sau đó gây lãng phí tính toán.
5. Client contract:
   - FE không được tự động retry khi gặp lỗi mạng/timeout để tránh nghẽn hàng đợi AI.
6. Hiện tại:
   - Chưa triển khai worker hay logic điều phối thật trong bước này.
   - Mọi phương thức trả về NotImplementedError hoặc trạng thái chờ tích hợp.
"""

from typing import TYPE_CHECKING, Any, Dict, List
import logging

from app.config import get_settings

if TYPE_CHECKING:
    import PIL.Image

logger = logging.getLogger("app.ai.model_manager")
settings = get_settings()


class ModelManager:
    """Bộ điều phối nạp, chuyển đổi và suy luận các mô hình AI VQA."""

    def __init__(self) -> None:
        self._current_model_id: str | None = None
        self._current_model_instance: Any = None
        self._initialized: bool = False

    async def startup(self) -> None:
        """Khởi tạo tài nguyên AI khi backend startup.

        TODO (Người 7 triển khai):
        - Chuẩn bị lock điều phối.
        - Kiểm tra tính sẵn sàng của thư mục model_artifacts.
        """
        raise NotImplementedError("ModelManager.startup đang chờ Người 7 triển khai.")

    async def predict(self, model_id: str, image: Any, question: str) -> str:
        """Điều phối suy luận an toàn cho một câu hỏi và ảnh.

        TODO (Người 7 triển khai):
        - Thu nhận lock điều phối duy nhất.
        - Kiểm tra nếu model_id != current_model_id thì tiến hành unload model cũ và load model mới.
        - Gọi adapter.predict trong worker thread qua asyncio.to_thread.
        - Bắt và xử lý timeout, đảm bảo không ngắt giữa chừng khi tài nguyên chưa giải phóng.
        - Trả về câu trả lời dạng chuỗi.
        """
        raise NotImplementedError("ModelManager.predict đang chờ Người 7 triển khai.")

    def list_models(self) -> List[Dict[str, Any]]:
        """Trả về danh sách model cùng trạng thái thực tế.

        TODO (Người 7 triển khai):
        - Trả về thông tin thực tế: scratch và finetuned kèm load_state (unloaded/loading/ready/error).
        """
        raise NotImplementedError("ModelManager.list_models đang chờ Người 7 triển khai.")

    async def shutdown(self) -> None:
        """Dọn dẹp và giải phóng tài nguyên AI khi backend tắt.

        TODO (Người 7 triển khai):
        - Chờ lượt inference hiện tại hoàn tất (nếu có).
        - Gọi unload() trên model đang nạp.
        - Giải phóng cache CUDA/RAM.
        """
        raise NotImplementedError("ModelManager.shutdown đang chờ Người 7 triển khai.")


# Instance singleton của ModelManager sẽ được Người 7 hoàn thiện và khởi tạo
model_manager = ModelManager()
