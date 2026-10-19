# Hướng dẫn cài đặt và chạy dự án AI Văn hóa (VQA)

Dự án gồm hai phần:

| Phần | Thư mục | Công nghệ | Địa chỉ khi chạy |
| --- | --- | --- | --- |
| Backend (API + model AI) | `backend/` | FastAPI, PyTorch, Transformers | http://127.0.0.1:8000 |
| Front-end (giao diện chat) | `Front-end/` | Streamlit | http://localhost:8501 |

Backend phục vụ hai model hỏi đáp hình ảnh:

- **`scratch`**: ResNet101 + ViT5, nhóm tự huấn luyện. Chạy hoàn toàn offline.
- **`finetuned`**: Vintern-1B-v2 đã fine-tune. Lần đầu nạp sẽ tải model nền `5CD-AI/Vintern-1B-v2` (~3,5 GB) từ Hugging Face.

---

## 0. Yêu cầu máy

- **Windows 10/11** (các lệnh dưới đây dùng PowerShell hoặc CMD).
- **Python 3.12 (64-bit)**. Đây là phiên bản đã chạy được cả hai model. Không dùng 3.13/3.14.
- **Dung lượng ổ đĩa trống:** khoảng 12 GB (trọng số ~3 GB, model nền Vintern ~3,5 GB, PyTorch ~3–5 GB).
- **GPU NVIDIA (khuyến nghị):** khi có GPU, model `finetuned` chạy nhanh hơn nhiều. Nếu không có GPU vẫn chạy được bằng CPU, nhưng cần nhiều RAM (nên có từ 16 GB) và mỗi câu trả lời mất khá lâu.
- **Git**, để clone mã nguồn.

Kiểm tra Python:

```powershell
python --version
```

Lệnh phải in ra `Python 3.12.x`. Nếu chưa có, tải Python 3.12 tại https://www.python.org/downloads/ và nhớ tick **"Add python.exe to PATH"** khi cài.

> Nếu máy cài nhiều bản Python và `python` không trỏ tới 3.12, hãy thay `python` bằng `py -3.12` trong mọi lệnh bên dưới.

---

## 1. Lấy mã nguồn

```powershell
git clone https://github.com/haiphong2206win-collab/AI_Van_hoa.git
cd AI_Van_hoa
```

Cấu trúc chính:

```
AI_Van_hoa/
├── backend/
│   ├── app/                 # mã nguồn API + adapter model
│   ├── model_artifacts/
│   │   ├── scratch/         # ← đặt trọng số model scratch vào đây
│   │   └── finetuned/       # ← đặt trọng số model finetuned vào đây
│   ├── requirements.txt
│   └── .env.example
└── Front-end/
    ├── app.py
    ├── requirements.txt
    └── .env.example
```

---

## 2. Cài thư viện

Chạy các lệnh sau ở thư mục gốc `AI_Van_hoa/`.

### 2.1. Cài PyTorch (chọn MỘT trong hai)

**Máy có GPU NVIDIA** (cần driver NVIDIA mới, hỗ trợ CUDA 12.8):

```powershell
python -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
```

**Máy không có GPU (chỉ CPU):**

```powershell
python -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
```

Kiểm tra:

```powershell
python -c "import torch; print(torch.__version__, 'CUDA:', torch.cuda.is_available())"
```

Bản GPU phải in ra `CUDA: True`. Nếu in `False`, hãy cập nhật driver NVIDIA hoặc dùng bản CPU.

### 2.2. Cài thư viện AI

Phải giữ đúng các phiên bản dưới đây. Code nạp model đã được kiểm tra với `transformers 4.46.3`; bản mới hơn có thể làm hỏng remote code của Vintern.

```powershell
python -m pip install transformers==4.46.3 tokenizers==0.20.3 sentencepiece==0.2.0 protobuf==5.29.3 timm einops accelerate
```

### 2.3. Cài thư viện backend và front-end

```powershell
python -m pip install -r backend\requirements-dev.txt
python -m pip install -r Front-end\requirements.txt
```

---

## 3. Tải và đặt trọng số model

Các file trọng số **không có trong Git** vì quá nặng. Tải chúng từ Google Drive:

👉 **https://drive.google.com/drive/folders/11gkRIeSiXK9GbPBsSFjQgd6O59G3b7P8**

### 3.1. Cách tải

**Cách A: tải bằng trình duyệt.** Mở link, bấm chuột phải vào từng thư mục hoặc file rồi chọn **Tải xuống**. Google Drive sẽ nén thành `.zip`; giải nén ra trước khi đặt file.

**Cách B: tải bằng lệnh `gdown`.**

```powershell
python -m pip install gdown
python -m gdown --folder https://drive.google.com/drive/folders/11gkRIeSiXK9GbPBsSFjQgd6O59G3b7P8 -O weights_download
```

Sau đó chép các file từ `weights_download\` vào đúng vị trí ở bước 3.2.

> Nếu `gdown` báo lỗi quota hoặc "Too many users have viewed or downloaded", hãy dùng cách A.

### 3.2. Đặt file đúng vị trí

Sau khi đặt xong, thư mục `backend\model_artifacts\` phải **đúng như sau**:

```
backend/model_artifacts/
├── scratch/
│   ├── best_vqa_model.pt            (~1,0 GB)
│   ├── manifest.json
│   └── vit5/
│       ├── added_tokens.json
│       ├── config.json
│       ├── generation_config.json
│       ├── special_tokens_map.json
│       ├── spiece.model
│       └── tokenizer_config.json
└── finetuned/
    └── best_vintern_vqa.pt          (~1,8 GB)
```

Lưu ý quan trọng:

- **Không đổi tên file.** Backend tìm đúng tên `best_vqa_model.pt` và `best_vintern_vqa.pt`.
- Thư mục `vit5/` phải nằm **bên trong** `scratch/`. Khi giải nén từ zip, đừng để bị lồng thêm một cấp (ví dụ `scratch/scratch/vit5`).
- `manifest.json` chứa mã SHA-256 của từng file. Model scratch sẽ kiểm tra mã này khi nạp, nên file tải về bị lỗi hoặc thiếu sẽ bị phát hiện ngay.

### 3.3. Model nền Vintern-1B-v2 (cho model `finetuned`)

File `best_vintern_vqa.pt` chỉ là phần trọng số đã fine-tune. Nó cần được nạp lên model nền **`5CD-AI/Vintern-1B-v2`** từ Hugging Face. Có hai cách:

**Cách 1: tự động (mặc định).** Lần đầu bạn chọn model `finetuned` trên giao diện, backend sẽ tự tải khoảng 3,5 GB về `C:\Users\<tên>\.cache\huggingface\hub`. Lần tải này cần Internet và có thể mất vài phút. Những lần sau backend dùng lại bản đã lưu.

**Cách 2: tải trước (khuyến nghị),** để lần chạy đầu không phải chờ:

```powershell
python -c "from huggingface_hub import snapshot_download; print(snapshot_download('5CD-AI/Vintern-1B-v2'))"
```

**Chạy offline hoặc để model nền ở ổ khác:** tải model nền vào một thư mục (ví dụ `D:\models\Vintern-1B-v2`) rồi thêm dòng sau vào `backend\.env`:

```
VINTERN_BASE=D:\models\Vintern-1B-v2
```

> Muốn đổi nơi lưu cache Hugging Face sang ổ khác (vì ổ C đầy), đặt biến môi trường `HF_HOME`, ví dụ `setx HF_HOME D:\hf_cache`, rồi mở lại terminal.

---

## 4. Cấu hình file `.env`

### 4.1. Backend

```powershell
copy backend\.env.example backend\.env
```

Mở `backend\.env` và sửa dòng `AI_DEVICE` theo máy của bạn:

| Máy | Giá trị |
| --- | --- |
| Có GPU NVIDIA (đã cài torch bản CUDA) | `AI_DEVICE=cuda` |
| Chỉ có CPU | `AI_DEVICE=cpu` |

Các biến còn lại có thể giữ nguyên:

| Biến | Ý nghĩa | Mặc định |
| --- | --- | --- |
| `SCRATCH_MODEL_PATH` | Thư mục trọng số scratch (tính từ `backend/`) | `model_artifacts/scratch` |
| `FINETUNED_MODEL_PATH` | Thư mục hoặc file trọng số finetuned | `model_artifacts/finetuned` |
| `VINTERN_BASE` | (tùy chọn) Thư mục model nền Vintern offline | `5CD-AI/Vintern-1B-v2` |
| `MAX_UPLOAD_BYTES` | Dung lượng ảnh tối đa | 10 MB |
| `INFERENCE_TIMEOUT_SECONDS` | Thời gian chờ tối đa mỗi câu hỏi | 180 |

> Trên CPU, model `finetuned` có thể cần hơn 180 giây cho mỗi câu trả lời. Nếu gặp lỗi timeout, tăng `INFERENCE_TIMEOUT_SECONDS` (ví dụ `600`).

### 4.2. Front-end

```powershell
copy Front-end\.env.example Front-end\.env
```

File chỉ có một dòng `API_BASE_URL=http://127.0.0.1:8000/api/v1`. Giữ nguyên, trừ khi bạn đổi cổng backend.

---

## 5. Chạy dự án

Cần mở **hai cửa sổ terminal**: một cho backend, một cho front-end. Thay đường dẫn bên dưới bằng nơi bạn đặt dự án.

### Terminal 1: Backend

```powershell
cd "D:\Documents\python\VietCulture AI\AI_Van_hoa\backend"
python -m uvicorn app.main:app
```

Khi thấy dòng `Application startup complete.` là backend đã sẵn sàng. Kiểm tra:

- http://127.0.0.1:8000/api/v1/health: trả về `{"status":"ok"}`
- http://127.0.0.1:8000/api/v1/models: cả hai model phải có `"available": true`. Nếu là `false` thì file trọng số chưa đặt đúng chỗ (xem bước 3.2).
- http://127.0.0.1:8000/docs: trang Swagger để thử API trực tiếp

> **Không** thêm `--reload` hay `--workers` khi chạy model thật. `--reload` có thể khởi động lại server giữa lúc đang suy luận. `--workers` thì nạp mỗi tiến trình một bản model, rất dễ tràn RAM/VRAM.

### Terminal 2: Front-end

```powershell
cd "D:\Documents\python\VietCulture AI\AI_Van_hoa\Front-end"
streamlit run app.py
```

Trình duyệt sẽ tự mở http://localhost:8501. Chọn model, tải ảnh lên và đặt câu hỏi.

> Nếu báo `streamlit is not recognized`, dùng `python -m streamlit run app.py`.

> Model chỉ được nạp vào bộ nhớ ở **câu hỏi đầu tiên**, không nạp lúc khởi động. Vì vậy câu đầu tiên sẽ chậm (vài chục giây trên GPU, lâu hơn trên CPU); các câu sau nhanh hơn. Mỗi lần đổi qua lại giữa `scratch` và `finetuned`, model cũ được giải phóng và model mới được nạp lại.

---

## 6. Kiểm tra (tùy chọn)

Chạy bộ test tự động của backend (trong thư mục `backend`):

```powershell
python -m pytest tests -v
```

Thử model scratch với một ảnh mà không cần web (trong thư mục `backend`):

```powershell
python tools\scratch\run_scratch.py --model-path model_artifacts/scratch --device cpu --image "D:\anh\demo.jpg" --question "Đây là gì?"
```

---

## 7. Lỗi thường gặp

| Hiện tượng | Nguyên nhân và cách xử lý |
| --- | --- |
| `/models` báo `"available": false` | Thiếu file hoặc sai tên/vị trí trọng số. Đối chiếu lại cây thư mục ở bước 3.2. |
| Lỗi 503 `MODEL_UNAVAILABLE` khi hỏi | Model nạp thất bại. Xem log ở Terminal 1. Thường do thiếu file, sai checksum (file tải bị lỗi, hãy tải lại), hoặc sai phiên bản `transformers` (phải là `4.46.3`). |
| `Torch not compiled with CUDA enabled` | Đặt `AI_DEVICE=cuda` nhưng lại cài torch bản CPU. Cài lại theo bước 2.1 (bản GPU) hoặc đổi thành `AI_DEVICE=cpu`. |
| `CUDA out of memory` | GPU không đủ VRAM. Đóng ứng dụng khác đang dùng GPU, hoặc chuyển sang `AI_DEVICE=cpu`. |
| `ModuleNotFoundError: timm` / `einops` | Chưa cài đủ thư viện ở bước 2.2. |
| `No module named uvicorn` / `streamlit` | Chưa cài thư viện ở bước 2.3, hoặc `python` đang trỏ tới bản Python khác bản đã cài thư viện. |
| Lần đầu dùng `finetuned` bị treo lâu | Backend đang tải model nền Vintern (~3,5 GB). Chờ tải xong, hoặc tải trước theo bước 3.3. |
| Lỗi timeout (504) trên CPU | Tăng `INFERENCE_TIMEOUT_SECONDS` trong `backend\.env`, rồi khởi động lại backend. |
| Front-end báo không kết nối được backend | Backend chưa chạy hoặc sai `API_BASE_URL` trong `Front-end\.env`. |

---

```
