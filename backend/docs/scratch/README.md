# Scratch VQA — Nguyễn Minh Quyền (người 5)

Bản tích hợp theo repository `haiphong2206win-collab/AI_Van_hoa`, nhánh main commit
`7a36e57`, kiểm tra ngày 07/10/2026. Đã nối BaseVIVQAModel, Settings và AppError thật.
Chưa có checkpoint/tokenizer của nhóm; chưa nghiệm thu suy luận thật hoặc luồng FE.

## Giao diện đã khớp repository

```python
from app.ai.scratch_model import ScratchVIVQAModel

model = ScratchVIVQAModel()  # đọc get_settings(): .env + biến môi trường
model.load()
answer = model.predict(rgb_image, normalized_question)  # str không rỗng
model.unload()
```

Manager chạy ba hàm sync trong worker tuần tự và chỉ unload sau khi worker thực sự
kết thúc. Adapter không đóng ảnh. Constructor không nạp AI/trọng số. `load()` gọi
lặp dùng lại model; predict trước load ném AppError 503 MODEL_UNAVAILABLE. `_is_loaded`
và `loaded` phản ánh cùng trạng thái thực; `artifacts_present()` chỉ kiểm tra sơ bộ.
Có thể truyền model_path/device trực tiếp khi thử độc lập. ScratchModel là alias
cho bộ công cụ cũ, không tạo thêm cache. Đã bỏ singleton/wrapper cấp module.

Các thay đổi nằm trong adapter của người 5 cùng các file mới `tools/scratch/` và
`docs/scratch/`. Không thay file của thành viên khác hay requirements chung.

## 2. Cài môi trường thử độc lập

Môi trường đã thử: Python **3.12.14**, Linux, CPU. Các phiên bản cụ thể trong kết quả test; Windows và CUDA chưa thử. Không dùng môi trường Python 3.14.2 của khung BE để suy ra hai model tương thích.

Trên Windows, dùng Python 3.12 đã cài. Mở PowerShell ở thư mục `backend` của repo:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r tools/scratch/requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tools/scratch/tests -v
.\.venv\Scripts\python.exe -m pytest tests tools/scratch/tests -q
```

Nếu lệnh `python` trỏ phiên bản khác, thay bằng đường dẫn đầy đủ tới Python 3.12. Không cần activate venv vì các lệnh đã gọi đúng interpreter.

Trên Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r tools/scratch/requirements.txt
.venv/bin/python -m unittest discover -s tools/scratch/tests -v
.venv/bin/python -m pytest tests tools/scratch/tests -q
```

Nếu máy có NVIDIA GPU và driver phù hợp, cài bộ wheel CUDA tương ứng thay cho CPU; ví dụ cặp được PyTorch công bố cho CUDA 12.4:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
```

Đây là hướng dẫn cài, chưa phải xác nhận chạy CUDA thành công. `AI_DEVICE=cpu` là mặc định; `cuda`, `cuda:0`… phải được yêu cầu rõ. Thiết bị không hỗ trợ sẽ báo lỗi, không tự âm thầm chuyển CPU. Adapter chạy FP32; chưa tối ưu FP16/BF16 để tránh thay đổi kết quả trước khi đối chiếu model thật.

Nguồn đối chiếu cặp framework: [PyTorch Previous Versions](https://docs.pytorch.org/get-started/previous-versions/). Không cần torchaudio cho scratch.

**Xung đột dependency cần người 1 và người 6 chốt:** notebook scratch chạy Transformers 4.46.3; `requirements.txt` nguồn ghi 4.44.2/tokenizers 0.19.1; notebook Vintern lưu output 5.0.0 cùng nhiều monkey-patch. Gói này chỉ kiểm thử 4.46.3/tokenizers 0.20.3 cho scratch. Chưa xác nhận một môi trường chung chạy được cả hai model. Không gộp hai requirements bằng cách cài đè liên tiếp.

## 3. Nhận và đặt artifact

Đường dẫn mặc định tính từ thư mục `backend`, không phụ thuộc nơi mở terminal:

| Đường dẫn dưới `backend/model_artifacts/scratch/` | Nội dung |
| --- | --- |
| `best_vqa_model.pt` | Toàn bộ `model_state_dict`, bao gồm cả ResNet101 và ViT5, cùng metadata/config |
| `vit5/config.json` | Cấu hình đúng ViT5 dùng khi train |
| `vit5/generation_config.json` | Thông số generation gốc |
| `vit5/spiece.model` | Vocabulary SentencePiece đúng của checkpoint |
| `vit5/tokenizer_config.json` | Cấu hình tokenizer slow/legacy, padding, special tokens |
| `vit5/special_tokens_map.json` | Mapping token đặc biệt |
| File tokenizer bổ sung do `save_pretrained` tạo ra | Giữ nguyên nếu có, ví dụ `added_tokens.json` |
| `manifest.json` | Kiến trúc, chế độ input, `min_new_tokens`, checksum và môi trường xuất |

Vocabulary nằm trong tokenizer. **Không cần `answer2id.json`/`id2answer.json`**: model này sinh token tự do, không phân loại vào danh sách đáp án. Không dùng tokenizer XLM-R của captioning hoặc báo cáo cũ.

Không cần tải lại `pytorch_model.bin`/`model.safetensors` của ViT5 hay trọng số ImageNet riêng khi startup: checkpoint đầy đủ đã chứa chúng. Adapter tạo kiến trúc từ local config và nạp `strict=True`; không có nhánh chạy với trọng số ngẫu nhiên nếu thiếu checkpoint.

### Xuất từ notebook đã train

Đưa `tools/scratch/export_scratch_artifacts.py` vào thư mục notebook và chạy cell sau trong môi trường đang có `tokenizer`, `model`, `CFG` từ notebook VQA scratch:

```python
from export_scratch_artifacts import export_scratch_artifacts

bundle = export_scratch_artifacts(
    checkpoint_path=CFG.CKPT_PATH,  # /kaggle/working/outputs/best_vqa_model.pt
    tokenizer=tokenizer,
    seq2seq_config=model.seq2seq.config,
    generation_config=model.seq2seq.generation_config,
    output_dir="/kaggle/working/scratch_export",
    min_new_tokens=0,  # khớp notebook; script scratch_model.py cũ dùng 5
)
print(bundle)
```

Hàm lấy trọng số từ checkpoint tốt nhất trên đĩa, không lấy trạng thái epoch cuối còn ở RAM. Xuất kèm đúng tokenizer/config từ cùng lần train. Dùng thư mục output mới/rỗng; nếu xuất lỗi, chọn thư mục mới khi chạy lại. Không huấn luyện lại model.

Sau đó tải cả thư mục `scratch_export`, đặt nội dung vào `backend/model_artifacts/scratch`. Không chỉ đổi tên checkpoint rồi bỏ qua tokenizer/config/manifest. `best_scratch_vqa.pt` trong script cũ chỉ là tên khác; chỉ dùng khi bên AI xác nhận đó là cùng checkpoint kiến trúc ResNet101 + ViT5.

Exporter và loader dùng `torch.load(..., weights_only=True)`. Nếu checkpoint cũ chứa `Path`/đối tượng Python không được hỗ trợ, bên AI cần xuất lại thành dict tensor + kiểu cơ bản tại môi trường tin cậy; không tự chuyển web loader sang `weights_only=False`.

## 4. Chạy một ảnh thật

Ở `backend`, sau khi nhận đủ artifact:

```powershell
.\.venv\Scripts\python.exe tools/scratch/run_scratch.py --model-path model_artifacts/scratch --device cpu --image "D:/images/demo.jpg" --question "Đây là gì?"
```

Đường dẫn ảnh ở ví dụ phải được thay bằng ảnh thật. CLI chuẩn hoá NFC + strip câu hỏi, sửa EXIF, ghép nền trắng cho alpha và chuyển RGB. Nó chỉ là công cụ local, không thay thế validation/giới hạn upload của người 2/3.

CLI in JSON chứa câu trả lời thực, thời gian load/inference, RSS process đo mẫu mỗi 20ms, peak VRAM nếu CUDA và trạng thái unload. Không có artifact: `status=BLOCKED`, exit code 2. Suy luận lỗi: exit code 1. Thành công: exit code 0. Các trường đo đạc chỉ ở CLI, **không thêm vào response HTTP**.

Đối chiếu đáp án mà bên AI đã chạy trên chính ảnh/câu hỏi đó:

```powershell
.\.venv\Scripts\python.exe tools/scratch/run_scratch.py --device cpu --image "D:/images/demo.jpg" --question "Đây là gì?" --reference-answer "CÂU TRẢ LỜI THỰC TỪ SCRIPT THAM CHIẾU"
```

Không dùng đáp án ground truth thay cho output của script khi kiểm tra parity. Cùng checkpoint/tokenizer/input/decode/device/dtype; nếu notebook đánh giá bằng autocast trên GPU, cần chạy tham chiếu FP32 trước khi kết luận adapter khác. `REFERENCE_MISMATCH` trả exit code 1. Chất lượng đúng/sai so với ground truth là một bước nghiệm thu riêng.


## Những việc còn chờ

1. Nhận artifact đầy đủ theo bảng trên; file notebook không chứa weights. Model
   trong code nguồn là ResNet101 + ViT5 pretrained, khác báo cáo ResNet50/Transformer
   thuần. Không nạp checkpoint captioning hoặc kiến trúc cũ vào adapter này.
2. Train/eval notebook có category/keyword/KB, API chỉ ảnh + câu hỏi. Adapter dùng
   question-only như hàm infer mẫu cell 48; không tự tạo metadata hay thêm field API.
   Bên AI cần xác nhận chất lượng ở chế độ này. Ví dụ có sẵn cuối notebook trả sai
   ảnh “Xe bò”; đó không phải kết quả kiểm thử mới của adapter.
3. Chốt decoding: notebook không ép min_new_tokens; script cũ ép 5. Export mặc định
   0 khớp notebook; dùng 5 chỉ khi bên AI chọn script cũ làm chuẩn. Không dùng output
   giải thích làm đáp án nếu sau marker Trả lời: rỗng.
4. Người 7 triển khai manager; người 1 nối lifespan; người 4/7 chốt ai sở hữu ảnh sau
   khi nhận request. Nhánh `feature/phan-trong-trung-api-hoi-ai` hiện đóng ảnh trong
   finally, còn tài liệu Word quy định manager sở hữu ảnh sau bàn giao. Nếu worker
   còn chạy sau timeout/cancel mà dùng chính ảnh đó, việc đóng ảnh sẽ không an toàn.
   Cần thống nhất copy ảnh tại manager hoặc bàn giao quyền sở hữu; adapter không
   tự đóng/copy ảnh hay tự quản lý timeout để che vấn đề này.
5. `.gitignore` hiện tại của repository chưa ignore model_artifacts/*.pt; trước khi
   đặt weights người 1 cần bổ sung rule. Phần này không stage/commit artifact.
6. Đọc `TEST_RESULTS.md` để phân biệt test kỹ thuật tổng hợp với checkpoint thật.

## Kiểm tra ghép nhánh

Làm trên `feature/nguyen-minh-quyen-scratch-model`, PR vào main để lead review.
Main hiện tại còn placeholder predict/models và manager; không coi test nền pass
là AI đã chạy được. File người 4 và file người 5 khác nhau, nhưng không có xung đột
Git không chứng minh tương thích timeout/quyền sở hữu ảnh lúc chạy.
