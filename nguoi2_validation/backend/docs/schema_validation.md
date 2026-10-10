# Schema, kiểm tra đầu vào và mẫu gọi API (Người 2)

Phạm vi file: `app/schemas/{prediction,model,error}.py`, `app/services/validation_service.py`, `tests/test_validation.py`, `examples/call_api.py`.
Nhánh gợi ý: `feature/validation`.

## 1. Quy tắc kiểm tra

| Trường | Quy tắc | Sai thì |
| :--- | :--- | :--- |
| `question` | Chuẩn hóa NFC, strip hai đầu; giữ nội dung và xuống dòng bên trong; không đổi hoa/thường. Độ dài **sau chuẩn hóa** từ 1 đến 2000 ký tự Python (`MAX_QUESTION_LENGTH`) | 422 `VALIDATION_ERROR` |
| `model_id` | Đúng `scratch` hoặc `finetuned`, chữ thường, không khoảng trắng; không tự sửa | 422 `VALIDATION_ERROR` |
| thiếu `file`/`question`/`model_id` | FastAPI báo qua handler chung của người 1 | 422 `VALIDATION_ERROR` |

Thông báo cố định (đã có test):

- `Câu hỏi không được để trống.`
- `Câu hỏi không được vượt quá 2000 ký tự.`
- `model_id không hợp lệ. Chỉ chấp nhận: scratch, finetuned.`

Giao diện (hàm thuần, không mở ảnh, không gọi model):

```python
validate_question(question: str) -> str   # trả về câu hỏi đã chuẩn hóa
validate_model_id(model_id: str) -> str   # trả về chính model_id nếu hợp lệ
```

Cách dùng trong endpoint (người 4): `normalized = validate_question(question)`; sai thì `AppError` tự bay lên handler chung, không bắt lại.

## 2. Schema

- `PredictionResponse`: `model_id`, `question`, `answer`. `extra="forbid"` nên không thêm `confidence`/`history`. `answer` không được rỗng hoặc toàn khoảng trắng.
- `ModelsResponse.models: list[ModelInfo]`, `ModelInfo`: `id` (`scratch`|`finetuned`), `name`, `available`, `load_state` (`unloaded`|`loading`|`ready`|`error`). Tên cũ `ModelItem`, `ModelListResponse` vẫn dùng được (alias).
- `ErrorResponse`: `{"error": {"code": str, "message": str}}`.
- `error_responses(413, 415, 422, 500, 503, 504)` trả dict cho `responses=` của route để Swagger hiện đủ lỗi.
- `MODEL_IDS` là tuple id hợp lệ, người 7 có thể dùng làm khóa registry.

## 3. Request và response mẫu

`POST /api/v1/predict`, `multipart/form-data`, ba trường: `file`, `question`, `model_id`.

200:

```json
{"model_id": "scratch", "question": "Trong ảnh có gì?", "answer": "Câu trả lời thực tế từ model."}
```

`question` trong response là bản đã chuẩn hóa (ví dụ gửi `"  Trong ảnh có gì?  "` thì nhận `"Trong ảnh có gì?"`).

Lỗi (luôn một dạng):

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Câu hỏi không được để trống."}}
```

| HTTP | code | Nguồn |
| :--- | :--- | :--- |
| 413 | `IMAGE_TOO_LARGE` | người 3 |
| 415 | `INVALID_IMAGE` | người 3 |
| 422 | `VALIDATION_ERROR` | người 2 + handler nền |
| 503 | `MODEL_UNAVAILABLE` / `SERVICE_UNAVAILABLE` | người 5-7 / placeholder |
| 504 | `INFERENCE_TIMEOUT` | người 7 |
| 500 | `INFERENCE_FAILED` / `INTERNAL_SERVER_ERROR` | người 4-7 / handler nền |
| 404, 405 | `NOT_FOUND`, `METHOD_NOT_ALLOWED` | handler nền |

`GET /api/v1/models` 200:

```json
{
  "models": [
    {"id": "scratch", "name": "Model tự xây", "available": true, "load_state": "unloaded"},
    {"id": "finetuned", "name": "Model fine tune", "available": false, "load_state": "error"}
  ]
}
```

## 4. Ví dụ cho FE

```javascript
const API = "http://127.0.0.1:8000/api/v1";

class ApiError extends Error {
  constructor(message, status, code) { super(message); this.status = status; this.code = code; }
}

async function loadModels() {
  const res = await fetch(`${API}/models`);
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(body?.error?.message || `Không tải được model (${res.status})`, res.status, body?.error?.code);
  return body.models; // [{id, name, available, load_state}]
}

async function askAI(file, question, modelId) {
  const data = new FormData();
  data.append("file", file);
  data.append("question", question);
  data.append("model_id", modelId);

  // Không tự đặt Content-Type: trình duyệt tự thêm boundary.
  const res = await fetch(`${API}/predict`, { method: "POST", body: data });
  const body = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(body?.error?.message || `Yêu cầu thất bại (${res.status})`, res.status, body?.error?.code);
  }
  if (typeof body?.answer !== "string" || !body.answer.trim()) {
    throw new ApiError("Phản hồi AI không hợp lệ", res.status, null);
  }
  return body; // {model_id, question (đã chuẩn hóa), answer}
}

// Kiểm tra nhanh ở FE chỉ để UX; BE vẫn quyết định.
// Đếm theo ký tự Unicode (giống Python), không dùng .length vì emoji tính 2 đơn vị.
const tooLong = (text) => [...text.trim()].length > 2000;
```

### Python (requests)

Bản đầy đủ nằm ở `examples/call_api.py` (`pip install requests`):

```python
import requests

API = "http://127.0.0.1:8000/api/v1"

with open("anh.jpg", "rb") as f:
    # Không tự đặt Content-Type: requests tự thêm boundary.
    r = requests.post(
        f"{API}/predict",
        files={"file": ("anh.jpg", f)},
        data={"question": "Trong ảnh có gì?", "model_id": "scratch"},
        timeout=200,  # dài hơn deadline 180 giây của backend
    )

body = r.json()
if r.ok:
    print(body["answer"])
else:
    print(r.status_code, body["error"]["code"], body["error"]["message"])
```

Chạy nhanh: `python examples/call_api.py anh.jpg "Trong ảnh có gì?" scratch`. Hàm `ask_ai()` và `list_models()` ném `ApiError(status, code)` nên dùng được cho giao diện Python.

Xử lý theo `status`/`code`, không tự gửi lại khi 504 hoặc lỗi mạng:

- 422: hiện `error.message` cạnh ô nhập, giữ ảnh và câu hỏi.
- 413/415: yêu cầu chọn ảnh khác.
- 503: khóa model đó hoặc báo chọn model khác.
- 504, 500, mã lạ: hiện `error.message`, bật lại nút gửi.
- `fetch` ném `TypeError`: BE tắt, sai cổng hoặc CORS, khác với lỗi HTTP có JSON.

PowerShell:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/predict" `
  -F "file=@D:/images/demo.jpg" -F "question=Trong ảnh có gì?" -F "model_id=scratch"
```

## 5. Điểm cần thống nhất với người 1

1. **Tên mã lỗi đã khớp.** `app/errors.py` đang dùng đúng `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `INTERNAL_SERVER_ERROR`, `SERVICE_UNAVAILABLE`, `INFERENCE_TIMEOUT`, `IMAGE_TOO_LARGE`, `INVALID_IMAGE`, `VALIDATION_ERROR`. Có thể đóng điểm mở trong hợp đồng mục 9. `MODEL_UNAVAILABLE` và `INFERENCE_FAILED` do `AppError` của người 5-7 tự đặt, không có mặc định trong handler.
2. **`AppError` mặc định status 400.** Mọi nơi ném `AppError` phải truyền `status_code` rõ. Phần của người 2 luôn truyền 422.
3. **Thông báo 422 thiếu trường đang bằng tiếng Anh** (`file: Field required`) vì `validation_error_handler` nối `msg` của pydantic. FE hiển thị nguyên văn cho người dùng. Đề nghị người 1 đổi thành tiếng Việt, ví dụ `Thiếu trường bắt buộc: file`. Đây là file của người 1 nên chỉ đề xuất.
4. **Tên hiển thị fine tune:** `docs/api_contract.md` ghi `Model fine-tune`, bản phân công ghi `Model fine tune`. Chọn một (người 7 giữ registry, người 8 sửa docs). `name` chỉ để hiển thị nên không ảnh hưởng FE.
5. **`answer` rỗng:** nếu model trả chuỗi rỗng mà người 4 vẫn dựng `PredictionResponse`, pydantic sẽ lỗi và FE nhận 500 `INTERNAL_SERVER_ERROR`. Người 4 cần tự kiểm tra trước và ném `AppError(code="INFERENCE_FAILED", status_code=500)`.
6. **Chưa kiểm chứng:** form `question=""` (rỗng) có thể bị FastAPI coi là thiếu trường nên trả `file/question: Field required` thay vì `Câu hỏi không được để trống.`. Cả hai đều 422 `VALIDATION_ERROR`; người 4/8 xác nhận khi chạy endpoint thật. Nếu muốn luôn có thông báo tiếng Việt, khai báo `question: str = Form("")` rồi để `validate_question` xử lý.
