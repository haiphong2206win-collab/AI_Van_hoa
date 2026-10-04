"""Dịch vụ xử lý và xác thực hình ảnh (Image Service).

Người phụ trách triển khai chính: Người 3.
Mục tiêu: Đọc, giải mã và tiền xử lý ảnh an toàn từ UploadFile.

Giao diện dự kiến:
    async def read_image(file: UploadFile) -> "PIL.Image.Image"

Quy ước nghiệp vụ bắt buộc:
1. Định dạng hỗ trợ: JPEG, PNG, WEBP tĩnh (từ chối ảnh động gif, webp animated).
2. Kích thước tối đa: Không vượt quá Settings.MAX_UPLOAD_BYTES (mặc định 10 MiB).
3. Kiểm tra tính hợp lệ:
   - Đọc bytes theo khối (chunked streaming), kiểm tra dung lượng để tránh tràn RAM.
   - Kiểm tra magic bytes và tính toàn vẹn cấu trúc ảnh (loại trừ ảnh hỏng / file giả mạo).
4. Chuẩn hóa hình ảnh:
   - Xử lý xoay theo EXIF orientation.
   - Chuyển đổi định dạng màu về không gian RGB.
   - Gọi image.load() hoàn chỉnh để đảm bảo ảnh nằm trọn trong RAM trước khi trả về.
5. Phạm vi trách nhiệm:
   - KHÔNG thực hiện resize, rescale, normalize theo từng model ở đây (phần đó thuộc adapter của Người 5 & 6).
   - Quyền sở hữu tài nguyên: Người gọi hàm (route / AI manager) sở hữu instance PIL.Image được trả về
     và có trách nhiệm đóng ảnh (image.close()) sau khi quá trình suy luận kết thúc hoàn toàn.

Trạng thái hiện tại:
- Skeleton, chưa triển khai xử lý ảnh thực tế.
- Dùng NotImplementedError.
"""

from typing import TYPE_CHECKING, Any
from fastapi import UploadFile

from app.config import get_settings

if TYPE_CHECKING:
    import PIL.Image

settings = get_settings()


async def read_image(file: UploadFile) -> Any:
    """Đọc và kiểm tra file ảnh từ client.

    TODO (Người 3 triển khai):
    - Đọc stream từ file UploadFile.
    - Kiểm tra kích thước <= settings.MAX_UPLOAD_BYTES.
    - Xác thực định dạng ảnh (JPEG, PNG, WEBP).
    - Chuẩn hóa EXIF, chuyển sang RGB và gọi load().
    - Trả về đối tượng PIL.Image.Image.
    """
    raise NotImplementedError("read_image đang chờ Người 3 triển khai.")
