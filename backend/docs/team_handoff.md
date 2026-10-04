# TÀI LIỆU BÀN GIAO VÀ PHÂN CÔNG TRÁCH NHIỆM (TEAM HANDOFF)

**Dự án:** Image VQA Demo (Hỏi đáp hình ảnh với 2 mô hình AI)  
**Nhóm:** 8 thành viên  
**Trưởng nhóm (Lead):** Người 1  

---

## 1. Bảng Quyền Sở Hữu File (File Ownership Matrix)

| Thành viên | Trách nhiệm chính | Các file trực tiếp sở hữu & quản lý |
| :--- | :--- | :--- |
| **Người 1** *(Lead)* | Kiến trúc khung nền, cấu hình, xử lý lỗi, lifespan, gom dependency | `app/main.py`<br>`app/config.py`<br>`app/errors.py`<br>`app/api/router.py`<br>`app/api/routes/health.py`<br>Các file `__init__.py` ban đầu<br>`.env.example`, `.gitignore`<br>`requirements.txt`, `requirements-dev.txt`<br>README ban đầu<br>*Kết nối lifecycle của ModelManager sau khi Người 7 bàn giao.* |
| **Người 2** | Schemas Pydantic & Dịch vụ xác thực dữ liệu đầu vào | `app/schemas/prediction.py`<br>`app/schemas/model.py`<br>`app/schemas/error.py`<br>`app/services/validation_service.py`<br>*Chốt nội dung Request/Response trong docs/api_contract.md.* |
| **Người 3** | Xử lý ảnh an toàn và giải mã | `app/services/image_service.py` |
| **Người 4** | Endpoint suy luận VQA | `app/api/routes/predict.py` |
| **Người 5** | Adapter cho Model huấn luyện từ đầu (Scratch) | `app/ai/scratch_model.py` |
| **Người 6** | Adapter cho Model Fine-tuned | `app/ai/finetuned_model.py` |
| **Người 7** | Giao diện cơ sở AI, ModelManager & Endpoint Models | `app/ai/base.py`<br>`app/ai/model_manager.py`<br>`app/api/routes/models.py` |
| **Người 8** | Kiểm thử mở rộng, nghiệm thu hợp đồng & hoàn thiện tài liệu | Mở rộng `tests/` (`test_core.py`, v.v.)<br>Hoàn thiện `README.md` sau khi tích hợp<br>Đối chiếu `docs/api_contract.md` với API thực tế. |

---

## 2. Giao Diện & Hàm Kết Nối Dự Kiến (Interface Contract)

### 2.1. Người 2 (Validation Service)
- **File:** `app/services/validation_service.py`
- **Chữ ký hàm:**
  ```python
  def validate_question(question: str) -> str:
      """Trim khoảng trắng, kiểm tra 1 <= độ dài <= MAX_QUESTION_LENGTH."""
      ...

  def validate_model_id(model_id: str) -> str:
      """Kiểm tra model_id nằm trong ('scratch', 'finetuned')."""
      ...
  ```
- **Hợp tác:** Người 4 sẽ gọi hai hàm này trong `app/api/routes/predict.py`.

### 2.2. Người 3 (Image Service)
- **File:** `app/services/image_service.py`
- **Chữ ký hàm:**
  ```python
  async def read_image(file: UploadFile) -> "PIL.Image.Image":
      """Đọc chunked bytes, kiểm tra <= 10 MiB, format JPEG/PNG/WEBP tĩnh, xoay EXIF, RGB, load()."""
      ...
  ```
- **Hợp tác:** Người 4 gọi hàm này để nhận `PIL.Image.Image` và chuyển giao cho `ModelManager.predict`. Người 4 có trách nhiệm đóng ảnh sau khi inference hoàn tất.

### 2.3. Người 5 & Người 6 (Model Adapters)
- **Files:** `app/ai/scratch_model.py` & `app/ai/finetuned_model.py`
- **Kế thừa:** `BaseVIVQAModel` (`app/ai/base.py`)
- **Chữ ký đồng bộ:**
  ```python
  def load(self) -> None: ...
  def predict(self, image: "PIL.Image.Image", question: str) -> str: ...
  def unload(self) -> None: ...
  ```
- **Hợp tác:** Người 7 gọi các adapter này thông qua luồng điều phối của `ModelManager`.

### 2.4. Người 7 (Model Manager & Models Route)
- **Files:** `app/ai/model_manager.py` & `app/api/routes/models.py`
- **Chữ ký hàm:**
  ```python
  async def startup(self) -> None: ...
  async def predict(self, model_id: str, image: "PIL.Image.Image", question: str) -> str: ...
  def list_models(self) -> list: ...
  async def shutdown(self) -> None: ...
  ```
- **Quy tắc điều phối cốt lõi:**
  1. Đơn tiến trình & đơn lượt chạy: Chỉ một lượt AI chạy tại một thời điểm (dùng lock).
  2. Tái sử dụng model đã nạp, không nạp lại nếu không đổi `model_id`.
  3. Quản lý timeout: Khi HTTP timeout, luồng AI bên dưới vẫn phải chạy xong và tự dọn dẹp an toàn; không hủy dở dang làm rò rỉ RAM/VRAM hoặc đóng ảnh khi AI đang đọc.
  4. Hủy request chờ nếu quá hạn trước khi được nạp vào chạy.
- **Hợp tác:**
  - Người 1 kết nối `startup()` và `shutdown()` vào `lifespan` trong `app/main.py`.
  - Người 4 gọi `predict()` trong route predict.
  - Người 7 trực tiếp hoàn thiện route `app/api/routes/models.py`.

---

## 3. Bản Đồ Phối Hợp Giữa Các Thành Viên

```
[Client / FE]
      │
      ▼
[app/main.py] (Người 1)
      │
      ├──> [app/api/routes/health.py] (Người 1)
      │
      ├──> [app/api/routes/models.py] (Người 7) ────> [ModelManager] (Người 7)
      │
      └──> [app/api/routes/predict.py] (Người 4)
                 │
                 ├──> [validation_service] (Người 2)
                 │
                 ├──> [image_service] (Người 3)
                 │
                 └──> [ModelManager.predict] (Người 7)
                            │
                            ├──> [ScratchVIVQAModel] (Người 5)
                            └──> [FinetunedVIVQAModel] (Người 6)
```

---

## 4. Quy Trình Làm Việc Nhóm & Quy Tắc Quản Trị Chung

1. **Tuyệt đối không sửa file của người khác:**
   - Mỗi thành viên chỉ chỉnh sửa trong phạm vi file mình sở hữu được liệt kê ở Bảng Quyền Sở Hữu.
   - Không tự ý đổi tên route, tên hàm, chữ ký tham số hoặc trường JSON chung nếu chưa có sự thống nhất bằng văn bản giữa các bên liên quan.
2. **Quản lý Thư viện / Dependency:**
   - Thành viên KHÔNG tự ý sửa file `requirements.txt` hoặc `requirements-dev.txt`.
   - Khi cần thêm thư viện (VD: Người 3 cần `Pillow`, Người 5/6 cần `torch`), thành viên đề xuất trực tiếp với **Người 1**. Người 1 sẽ kiểm tra xung đột phiên bản và tổng hợp dependency.
3. **Quy chuẩn bàn giao code:**
   - Mỗi người khi hoàn thiện module phải bàn giao kèm:
     - Đoạn script hoặc unit test chạy thử độc lập cho module đó.
     - Danh sách thư viện cần thêm.
     - Danh sách lỗi còn tồn đọng hoặc điểm cần lưu ý.
   - Tự chịu trách nhiệm debug và sửa lỗi trong phạm vi module của mình sau khi ghép tích hợp.
4. **Quy tắc làm việc với Git (Áp dụng sau khi Người 1 khởi tạo repo):**
   - Không commit trực tiếp lên nhánh `main`.
   - Mỗi thành viên tạo nhánh riêng theo định dạng: `feature/<ten-thanh-vien>-<chuc-nang>` (Ví dụ: `feature/person3-image-service`).
   - Mở Pull Request (PR) và chỉ merge khi có ít nhất Người 1 (Lead) review và CI/test vượt qua.
