# Bàn giao: model fine-tune Vintern (Người 6)

## Đã đối chiếu với notebook của Minh

- Model nền: **Vintern-1B-v2** (`5CD-AI/Vintern-1B-v2`).
- Cách fine-tune: đóng băng vision backbone, cập nhật projector `mlp1` và language model; đây **không phải LoRA**.
- Checkpoint notebook lưu dưới dạng `best_vintern_vqa.pt`, dict có khóa `model_state_dict`, `epoch`, `val_loss`, `config`.
- Adapter backend nạp checkpoint state dict lên model nền; không cần bước merge LoRA.
- Tiền xử lý: RGB, resize 448×448 bicubic, ImageNet mean/std; prompt inference `<image>\n{question}`; sinh câu trả lời theo `max_new_tokens=128`, `num_beams=3`, `repetition_penalty=1.5`; tách phần sau `Trả lời:` nếu có.
- Notebook có category/keyword/cultural KB context, nhưng API backend hiện chỉ nhận ảnh và question. Khi thiếu metadata, notebook fallback sang câu hỏi nguyên văn; adapter này theo đúng fallback đó.

## Đặt artifact và cấu hình

Đặt checkpoint tại `backend/model_artifacts/finetuned/best_vintern_vqa.pt` (hoặc đặt `FINETUNED_MODEL_PATH` trỏ tới file/thư mục checkpoint). Không commit checkpoint lên Git.

`VINTERN_BASE` phải trỏ tới thư mục model nền Vintern-1B-v2 có đủ config, tokenizer, weights và các file Python remote-code cần thiết; mặc định code dùng `5CD-AI/Vintern-1B-v2`. Với deploy offline, hãy chuẩn bị model nền trong cache hoặc thư mục local và đặt `VINTERN_BASE` tương ứng. Model nền cũng không commit vào repo.

## Giao diện backend

`FinetunedVIVQAModel` triển khai `load() -> None`, `predict(image, question) -> str`, `unload() -> None` theo `BaseVIVQAModel`. `predict()` không đóng ảnh đầu vào. Thiếu checkpoint hoặc lỗi nạp -> `MODEL_UNAVAILABLE`/503; lỗi suy luận -> `INFERENCE_FAILED`/500.

## Kiểm tra

Từ thư mục `backend/`:

```powershell
python scripts/test_finetuned.py path\to\sample.jpg "Đây là gì?"
```

Cần có `torch`, `torchvision`, `transformers`, `Pillow`, model nền và checkpoint thật. Phiên bản thư viện, thiết bị, thời gian nạp/suy luận và ví dụ kết quả: **chưa được xác nhận lại bằng adapter backend**. Không ghi test pass cho tới khi lệnh chạy thành công trong môi trường nhóm.

## Việc còn lại trước khi báo hoàn tất

- [ ] Lấy checkpoint `.pt` thật từ Minh và xác nhận nó đúng định dạng notebook.
- [ ] Xác nhận thư mục/model nền Vintern v2 và phiên bản Transformers tương thích với remote code của notebook.
- [ ] Chạy script test trên máy có model và ảnh thật; ghi Python/thư viện/thiết bị/thời gian/kết quả.
- [ ] Phối hợp Phong/Người 7 để thử qua ModelManager.
- [ ] Đề xuất dependency mới cho Phong tổng hợp; không tự sửa `requirements.txt`.

## Lưu ý file huấn luyện cũ

`finetune_vintern.py` bản LoRA v3.5 trước đây không tạo ra checkpoint v2 của notebook Minh. Không đưa script đó vào PR như quy trình train hiện hành. Notebook `vqa-vintern.ipynb` là nguồn train/inference đã được đối chiếu.
