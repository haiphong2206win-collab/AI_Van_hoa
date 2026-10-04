# HỢP ĐỒNG GIAO TIẾP API (API CONTRACT)

**Dự án:** Image VQA Demo (Hỏi đáp tiếng Việt qua hình ảnh)  
**Tài liệu phụ trách:** Người 1 (khởi tạo nền ban đầu) & Người 2 (chốt chi tiết Schema) & Người 8 (đối chiếu nghiệm thu).  
**Phiên bản tài liệu:** 1.0.0  

---

## 1. Nguyên Tắc & Quy Ước Chung

- **Base URL:** `http://127.0.0.1:8000/api/v1`
- **Prefix đồng nhất:** `API_PREFIX` là `/api/v1` và chỉ được cấu hình duy nhất một lần ở root router. Tuyệt đối không lặp lại thành `/api/v1/api/v1`.
- **CORS & Origin:** `http://localhost:5500`, `http://127.0.0.1:5500`, `http://localhost:5173`, `http://127.0.0.1:5173`.
  > *Lưu ý quan trọng cho FE:* `localhost` và `127.0.0.1` là hai origin hoàn toàn khác nhau đối với trình duyệt.
- **Không Authentication / State:** Không sử dụng session, cookie, database hay token đăng nhập (`allow_credentials=False`).
- **Phạm vi hiện tại:**
  - Chưa hỗ trợ streaming token, webcam direct stream, batch inference.
  - Không lưu lịch sử trò chuyện trên backend. Frontend tự giữ tạm lịch sử hội thoại trên RAM/State.
  - Mỗi lượt hỏi đáp bao gồm đúng một ảnh và một câu hỏi. Frontend phải gửi lại file ảnh trong mỗi lần hỏi.
  - Khi người dùng bấm gửi, Frontend phải khóa nút gửi (disable submit) để tránh gửi lặp request.
  - Frontend tuyệt đối **không tự động retry** khi gặp lỗi mạng hoặc HTTP timeout (504).

---

## 2. Phân Biệt Trạng Thái Hiện Tại & Hợp Đồng Sau Tích Hợp

| Endpoint | Method | Trạng thái hiện tại (Pha nền tảng) | Trạng thái sau tích hợp (Pha hoàn thiện) |
| :--- | :---: | :--- | :--- |
| `/health` | `GET` | **Triển khai thật** (HTTP 200 `{"status": "ok"}`) | Giữ nguyên xác nhận tiến trình backend hoạt động |
| `/models` | `GET` | **Placeholder** (HTTP 503 `SERVICE_UNAVAILABLE`) | Trả danh sách model thực tế từ ModelManager |
| `/predict` | `POST` | **Placeholder** (HTTP 503 `SERVICE_UNAVAILABLE`) | Suy luận thật với model AI, trả về câu trả lời |

---

## 3. Cấu Trúc Lỗi Thống Nhất (Error Format)

Mọi phản hồi lỗi (HTTP 4xx, 5xx) đều tuân thủ định dạng JSON chuẩn:

```json
{
  "error": {
    "code": "TÊN_MÃ_LỖI",
    "message": "Thông tin mô tả lỗi dễ hiểu cho người dùng."
  }
}
```

Các mã lỗi chuẩn:
- `404 NOT_FOUND`: Tuyến API không tồn tại.
- `413 IMAGE_TOO_LARGE`: Dung lượng ảnh vượt quá giới hạn cho phép (mặc định > 10 MiB).
- `415 INVALID_IMAGE`: Định dạng file không hợp lệ hoặc ảnh bị hỏng/giả mạo.
- `422 VALIDATION_ERROR`: Dữ liệu đầu vào thiếu hoặc không thỏa mãn ràng buộc nghiệp vụ.
- `503 SERVICE_UNAVAILABLE`: Tính năng đang chờ tích hợp hoặc dịch vụ tạm ngưng.
- `503 MODEL_UNAVAILABLE`: Model được yêu cầu chưa sẵn sàng hoặc gặp sự cố.
- `504 INFERENCE_TIMEOUT`: Quá thời gian suy luận cho phép (Settings.INFERENCE_TIMEOUT_SECONDS).
- `500 INFERENCE_FAILED`: Suy luận model AI thất bại do lỗi nội bộ.
- `500 INTERNAL_SERVER_ERROR`: Lỗi hệ thống không dự kiến (được log stack trace tại server, không lộ ra client).

---

## 4. Chi Tiết Các Endpoints

### 4.1. Health Check

Xác nhận tiến trình backend đang chạy.

- **URL:** `GET /api/v1/health`
- **Request Headers:** Không yêu cầu
- **Response HTTP 200:**
```json
{
  "status": "ok"
}
```

---

### 4.2. Danh Sách Model (Models List)

Lấy danh sách các model VQA được backend hỗ trợ cùng trạng thái nạp.

- **URL:** `GET /api/v1/models`
- **Trạng thái hiện tại:** HTTP 503 `SERVICE_UNAVAILABLE`
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Chức năng đang chờ tích hợp."
  }
}
```
- **Hợp đồng cuối cùng (Sau khi Người 7 tích hợp):**
  - **HTTP Status:** 200 OK
  - **Response Body:**
```json
{
  "models": [
    {
      "id": "scratch",
      "name": "Model tự xây",
      "available": false,
      "load_state": "unloaded"
    },
    {
      "id": "finetuned",
      "name": "Model fine-tune",
      "available": false,
      "load_state": "unloaded"
    }
  ]
}
```
  - `load_state` gồm 4 trạng thái:
    - `unloaded`: Model chưa được nạp vào bộ nhớ.
    - `loading`: Đang nạp trọng số vào RAM/VRAM.
    - `ready`: Đã nạp và sẵn sàng suy luận ngay lập tức.
    - `error`: Lỗi khi nạp trọng số.
  - `available` là `true` khi model sẵn sàng phục vụ.

---

### 4.3. Suy Luận VQA (Predict)

Gửi ảnh và câu hỏi để model AI trả lời.

- **URL:** `POST /api/v1/predict`
- **Content-Type:** `multipart/form-data`
  > *Lưu ý cho Frontend:* Khi dùng JavaScript `FormData`, **KHÔNG** tự gán header `Content-Type: multipart/form-data`. Trình duyệt hoặc HTTP client cần tự động thêm header kèm `boundary` phân tách chính xác.

- **Request Fields (Form Data):**
  - `file` *(bắt buộc, Binary)*: File ảnh định dạng JPEG, PNG, hoặc WEBP tĩnh. Dung lượng <= 10 MiB.
  - `question` *(bắt buộc, string)*: Câu hỏi bằng tiếng Việt, từ 1 đến 2000 ký tự (sẽ được trim khoảng trắng).
  - `model_id` *(bắt buộc, string)*: Mã model được chọn, chỉ chấp nhận một trong hai giá trị cố định: `"scratch"` hoặc `"finetuned"`.

- **Trạng thái hiện tại:**
  - Nhận request đúng cấu trúc -> trả HTTP 503 `SERVICE_UNAVAILABLE`:
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Chức năng đang chờ tích hợp."
  }
}
```
  - Thiếu trường bắt buộc (`file`, `question`, hoặc `model_id`) -> trả HTTP 422:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "file: Field required; model_id: Field required"
  }
}
```

- **Hợp đồng cuối cùng (Sau khi nhóm tích hợp hoàn tất):**
  - **HTTP Status:** 200 OK
  - **Response Body:**
```json
{
  "model_id": "scratch",
  "question": "Đây là địa danh nào?",
  "answer": "Chùa Một Cột tại Hà Nội."
}
```
