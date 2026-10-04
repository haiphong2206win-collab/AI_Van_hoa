# DỰ ÁN BACKEND WEB HỎI ĐÁP HÌNH ẢNH (IMAGE VQA DEMO)

Dự án backend cung cấp dịch vụ Web Hỏi Đáp dựa trên hình ảnh (Visual Question Answering - VQA) hỗ trợ hai mô hình AI:
1. `scratch`: Mô hình tự xây dựng và huấn luyện từ đầu.
2. `finetuned`: Mô hình pretrained được tinh chỉnh (fine-tuned) trên tập dữ liệu đặc thù.

Dự án được xây dựng với **Python** và **FastAPI**, chạy thử nghiệm cục bộ (local demo), hướng tới sự ổn định, rõ ràng và phân công mạch lạc cho nhóm 8 thành viên.

---

## 1. Phạm Vi Và Trạng Thái Hiện Tại

- **Phiên bản hiện tại:** Khung nền tảng (Foundation Scaffold do Người 1 - Lead thiết lập).
- **Trạng thái thực tế:**
  - Phần nền hoạt động hoàn chỉnh: Cấu hình biến môi trường (`pydantic-settings`), router tập trung `/api/v1`, xử lý lỗi thống nhất, middleware CORS, tài liệu tự động `/docs` và `/openapi.json`.
  - Endpoint `GET /api/v1/health`: **Đã triển khai thật**, trả về `{"status": "ok"}`.
  - Endpoint `GET /api/v1/models` và `POST /api/v1/predict`: **Placeholder**, trả về HTTP 503 `SERVICE_UNAVAILABLE`.
  - **Chưa có model AI và chưa nạp trọng số:** Hệ thống khởi động bình thường mà không cần model weights. Không sinh câu trả lời giả.
  - **Không database/ORM/Auth:** Không lưu lịch sử trò chuyện trên máy chủ; Frontend tự quản lý trạng thái hiển thị tạm.
  - **Chưa cài đặt PyTorch/Transformers:** Các thư viện AI nặng sẽ được bổ sung khi Người 5, 6, 7 tích hợp mô hình.

---

## 2. Môi Trường Hoạt Động

- **Hệ điều hành:** Windows (PowerShell / Command Prompt).
- **Phiên bản Python đã kiểm tra tương thích thực tế:** `Python 3.14.2` (64-bit).
- **Kiến trúc thư mục:** Thư mục làm việc của backend là `backend/`.

---

## 3. Hướng Dẫn Cài Đặt Cho Thành Viên Mới (Windows)

Mở terminal PowerShell hoặc Command Prompt và di chuyển vào thư mục `backend/`:

```powershell
cd d:\IT\Python\web_van_hoa\backend
```

### Bước 1: Tạo môi trường ảo (.venv)

```powershell
python -m venv .venv
```

> **Lưu ý quan trọng trên Windows (PowerShell):**  
> Nếu bạn gặp thông báo lỗi quyền thực thi kịch bản (Execution Policy) khi chạy `.\.venv\Scripts\Activate.ps1`, bạn **không cần thay đổi Execution Policy toàn máy**.  
> Thay vào đó, hãy gọi trực tiếp thông dịch viên Python của môi trường ảo:  
> `.\.venv\Scripts\python.exe <lệnh_cần_chạy>`

### Bước 2: Nâng cấp pip và cài đặt thư viện

Sử dụng trực tiếp interpreter trong `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Cài đặt các gói phụ thuộc cho phát triển và kiểm thử (đã bao gồm các gói nền trong `requirements.txt`):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### Bước 3: Thiết lập file cấu hình môi trường (.env)

Sao chép file mẫu `.env.example` thành `.env`:

```powershell
copy .env.example .env
```

Nội dung cấu hình mặc định trong `.env`:
- `APP_NAME=Image VQA Demo`
- `API_PREFIX=/api/v1`
- `HOST=127.0.0.1`
- `PORT=8000`
- `CORS_ORIGINS=["http://localhost:5500","http://127.0.0.1:5500","http://localhost:5173","http://127.0.0.1:5173"]` (Chuỗi JSON Array định nghĩa các nguồn gốc được phép)
- `SCRATCH_MODEL_PATH=model_artifacts/scratch`
- `FINETUNED_MODEL_PATH=model_artifacts/finetuned`
- `AI_DEVICE=cpu`
- `MAX_UPLOAD_BYTES=10485760` (10 MiB)
- `MAX_QUESTION_LENGTH=2000`
- `INFERENCE_TIMEOUT_SECONDS=180`
- `LOG_LEVEL=INFO`

> **Lưu ý về HOST và PORT:** Uvicorn CLI không tự động đọc HOST/PORT từ `.env`. Các tham số này được định nghĩa để quản lý tập trung và sử dụng khi chạy lệnh khởi động hoặc deploy script.

---

## 4. Hướng Dẫn Khởi Động Backend

Chạy lệnh sau từ thư mục `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Sau khi server khởi động:
- **Tài liệu Swagger UI tương tác:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON Schema:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **API Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) (Trả về `{"status":"ok"}`)

---

## 5. Chạy Kiểm Thử Tự Động (Automated Testing)

Chạy bộ kiểm thử nền tảng bằng `pytest`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Bộ kiểm thử bao gồm 11 bài test xác minh:
- Khởi động ứng dụng thành công khi chưa có trọng số model.
- Không trùng lặp tiền tố URL `/api/v1`.
- Điểm kiểm tra sức khỏe `GET /health` trả về chuẩn 200.
- Điểm kiểm tra placeholder `/models` và `/predict` trả về đúng 503 `SERVICE_UNAVAILABLE`.
- Kiểm tra tính đầy đủ của trường bắt buộc (thiếu dữ liệu trả về 422 `VALIDATION_ERROR`).
- Cơ chế CORS preflight và phản hồi lỗi (bao gồm lỗi 500) đảm bảo đầy đủ CORS headers mà không để lộ stack trace nhạy cảm.

---

## 6. Vị Trí Lưu Trữ Trọng Số Model (Artifacts) Sau Này

Khi nhóm AI huấn luyện xong các mô hình, các file trọng số (checkpoints, weights, tokenizer, config...) sẽ được đặt vào hai thư mục sau:
- Model Scratch: `backend/model_artifacts/scratch/`
- Model Fine-tuned: `backend/model_artifacts/finetuned/`

*(Các thư mục này hiện tại được giữ trong mã nguồn thông qua file `.gitkeep` và được bỏ qua các file trọng số nặng trong `.gitignore`)*.

---

## 7. Lưu Ý Cốt Lõi Khi Tích Hợp AI Thật (Dành Cho Toàn Nhóm)

1. **Đơn tiến trình (Single Process):**  
   Khi chạy suy luận AI với mô hình học sâu, phải chạy trên **1 tiến trình duy nhất** (không dùng cờ `--workers` với số lượng lớn) để tránh việc mỗi tiến trình nạp riêng một bản sao model gây tràn RAM/VRAM.
2. **Tránh `--reload` tự động trong môi trường đo đạc/suy luận:**  
   Cờ `--reload` giám sát file thay đổi và có thể khởi động lại server giữa chừng khi model đang chạy suy luận.
3. **Tuân thủ phân công:**  
   Vui lòng tham khảo tài liệu [docs/team_handoff.md](docs/team_handoff.md) để nắm rõ ranh giới quyền sở hữu file, chữ ký giao diện và nguyên tắc đóng góp mã nguồn.
