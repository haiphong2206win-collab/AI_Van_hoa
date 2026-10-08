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

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List

from app.config import get_settings
from app.ai.base import LoadState, MockVIVQAModel

if TYPE_CHECKING:
    import PIL.Image

logger = logging.getLogger("app.ai.model_manager")
settings = get_settings()

class ModelManager:
    """Bộ điều phối nạp, chuyển đổi và suy luận các mô hình AI VQA."""

    def __init__(self) -> None:
        self._current_model_id: str | None = None
        self._lock: asyncio.Lock | None = None
        self._initialized: bool = False
        
        self._registry = {
            "scratch": MockVIVQAModel(),
            "finetuned": MockVIVQAModel()
        }
        self._model_names = {
            "scratch": "Scratch Model (Tự huấn luyện)",
            "finetuned": "Fine-tuned Model (Chuyên biệt)"
        }

    async def startup(self) -> None:
        self._lock = asyncio.Lock()
        self._initialized = True
        logger.info("ModelManager đã sẵn sàng.")

    async def predict(self, model_id: str, image: Any, question: str) -> str:
        if not self._initialized or self._lock is None:
            image.close()
            raise RuntimeError("ModelManager chưa được khởi tạo.")
            
        if model_id not in self._registry:
            image.close()
            raise ValueError(f"Model ID '{model_id}' không tồn tại.")

        loop = asyncio.get_running_loop()
        deadline = loop.time() + settings.INFERENCE_TIMEOUT_SECONDS

        await self._lock.acquire()
        try:
            if loop.time() > deadline:
                logger.warning(f"Loại bỏ request do quá {settings.INFERENCE_TIMEOUT_SECONDS}s.")
                raise TimeoutError("Request quá hạn trong hàng đợi.")

            if self._current_model_id != model_id:
                if self._current_model_id is not None:
                    old_model = self._registry[self._current_model_id]
                    await asyncio.to_thread(old_model.unload)
                
                new_model = self._registry[model_id]
                await asyncio.to_thread(new_model.load)
                self._current_model_id = model_id

            model = self._registry[self._current_model_id]
            inference_task = asyncio.create_task(asyncio.to_thread(model.predict, image, question))
            
            try:
                result = await asyncio.shield(inference_task)
                return result
            except asyncio.CancelledError:
                logger.warning("Client ngắt kết nối. ĐANG CHỜ worker AI hoàn tất...")
                await inference_task 
                raise 
        finally:
            self._lock.release()
            image.close()

    def list_models(self) -> List[Dict[str, Any]]:
        result = []
        for m_id, model in self._registry.items():
            result.append({
                "id": m_id,
                "name": self._model_names.get(m_id, m_id),
                "available": True,
                "load_state": model.state.value
            })
        return result

    async def shutdown(self) -> None:
        if self._lock is not None:
            async with self._lock: 
                if self._current_model_id is not None:
                    model = self._registry[self._current_model_id]
                    if model.state == LoadState.READY:
                        await asyncio.to_thread(model.unload)
        self._initialized = False

model_manager = ModelManager()