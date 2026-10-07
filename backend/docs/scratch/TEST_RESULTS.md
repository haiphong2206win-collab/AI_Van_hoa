# Kết quả kiểm thử tích hợp scratch

Ngày 07/10/2026, Linux x86_64, Python 3.12.14, CPU; nền repository main `7a36e57`.

## Lệnh và kết quả

Tại `backend`:

```bash
.venv/bin/python -m pytest tests tools/scratch/tests -q
```

Kết quả: **23 passed, 5 warnings, 6 subtests passed in 11.42s**.
Gồm 11 test nền của repo, 9 test scratch độc lập và 3 test hợp đồng repository.

Các kiểm tra bao gồm:

- Import adapter không import torch/transformers hoặc nạp model.
- Khớp BaseVIVQAModel, Settings/.env, đường dẫn và AppError thực của repo.
- Thiếu artifact trả MODEL_UNAVAILABLE/503 qua error handler HTTP thật.
- Xuất và nạp bundle, kiểm tra checksum, trọng số thiếu, thiết bị không hợp lệ.
- Tensor xử lý ảnh, token câu hỏi, encoder input và generated IDs khớp code
  tham chiếu notebook trên fixture tổng hợp.
- Trả chuỗi đáp án, kiểm tra marker/rỗng; không đóng ảnh của caller.
- Giải phóng tham chiếu model và gọi unload lặp an toàn.
- CLI chạy suy luận fixture qua subprocess, xuất số đo và trạng thái unload.

5 cảnh báo deprecation từ bộ test/framework hiện có: Starlette TestClient với
httpx và tên hằng HTTP 422/413. Không có test thất bại; chưa sửa file chung của nhóm.

## Phiên bản đã chạy

| Thư viện | Phiên bản |
| --- | --- |
| torch / torchvision | 2.6.0+cpu / 0.21.0+cpu |
| transformers / tokenizers | 4.46.3 / 0.20.3 |
| sentencepiece | 0.2.0 |
| Pillow / protobuf / psutil | 12.3.0 / 5.29.3 / 7.0.0 |
| FastAPI / Starlette | 0.142.2 / 1.7.0 |
| pydantic / pydantic-settings | 2.13.5 / 2.15.0 |
| pytest / httpx | 9.1.1 / 0.28.1 |

## Giới hạn nghiệm thu

Fixture sử dụng ResNet101 đầy đủ với trọng số ngẫu nhiên, T5 rất nhỏ và tokenizer
SentencePiece huấn luyện trên dữ liệu giả. Không tải model từ mạng khi test.
Kết quả xác nhận cơ chế adapter và tương thích backend, **không xác nhận chất lượng
model đã huấn luyện**, tốc độ/RAM của ViT5-base thật hoặc độ chính xác VQA.

Chưa có checkpoint/tokenizer/config thật trong repository. Chưa thử CUDA,
Windows, chạy chung Vintern hoặc luồng FE → manager → model hoàn chỉnh; manager
và endpoints ở main còn placeholder. Không commit fixture weights hay dữ liệu nguồn.

Sau khi nhận bundle, chạy CLI trong README với ảnh/câu hỏi và đáp án tham chiếu
cùng checkpoint, rồi ghi thêm thời gian/RAM, kết quả parity và chất lượng thực tế.
