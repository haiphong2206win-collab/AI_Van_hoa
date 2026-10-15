# Đối chiếu 13 file nguồn ban đầu

Ghi chú 07/10: đã đọc repository và nối AppError/base/config thật; phần thiếu source BE bên dưới mô tả trạng thái lần bàn giao 05/10. Trạng thái hiện tại ở README.md trong cùng thư mục.

Đã đọc code/markdown của toàn bộ notebook, output text được lưu sẵn, các file Python/requirements, nội dung cả hai PDF và các đoạn văn/bảng Word. Đây là đối chiếu phục vụ triển khai adapter, không xác minh lại kết quả huấn luyện hoặc tất cả tài liệu khoa học được trích trong báo cáo.

| File người dùng gửi | Nội dung/điểm tác động |
| --- | --- |
| `img-cap.ipynb` | Image captioning song ngữ Flickr30k; ResNet50 + Transformer decoder tự train, XLM-R tokenizer, ảnh 224, 12 epochs, freeze 4 epochs. Không dùng checkpoint này cho VQA. |
| `vqa_scratch.ipynb` | Nguồn chính: ResNet101 pretrained khi train + ViT5-base pretrained, visual prefix 16 token, ảnh 512, question/answer length 96. Có train + eval + infer và output đã lưu. |
| `vqa-vintern.ipynb` | Model fine-tuned Vintern-1B-v2, InternViT + Qwen2; tokenizer/model khác scratch; ảnh 448 bicubic. Output ghi Transformers 5.0.0, GPU RTX PRO 6000 ~95 GB; nhiều patch toàn cục. Không áp dụng các patch đó cho scratch. |
| `app.py` | Gradio; run_vqa trả tuple, lịch sử chat frontend; hiển thị trực tiếp exception và `share=True`. Không phải khung FastAPI đích. |
| `registry.py` | Registry hai module, tên scratch mô tả “Transformer thuần” không khớp code ResNet101 + ViT5. Chưa có manager tuần tự/unload/timeout của hợp đồng. |
| `requirements.txt` | Ghim Transformers 4.44.2 và tokenizers 0.19.1; torch/torchvision chưa ghim. Khác notebook scratch 4.46.3 và Vintern output 5.0.0. |
| `scratch_model.py` | Nguồn infer tham chiếu: ResNet101 + ViT5, IMG_SIZE=512, q=96, gen=96, beams=4, min_new_tokens=5, trả tuple; tải base qua Hub, eager import AI, tự chọn CUDA, không unload. Adapter mới khắc phục phần lifecycle/hợp đồng. |
| `vintern_model.py` | Infer Vintern, bf16, ảnh 448, prompt `<image>`, tuple; fake flash_attn và patch Qwen. Phần người 6, không sửa. |
| `PY BTL - Sheet2.pdf` | Phân công Nguyễn Minh Quyền model tự xây, người 7 manager, người 4 HTTP, người 3 ảnh; demo local, không DB/lưu ảnh/lịch sử backend. |
| `bao_cao_vqa.pdf` | 54 trang PDF; báo cáo lý thuyết còn placeholder, mô tả ResNet50 + question encoder + fusion + Transformer decoder, XLM-R; khác code scratch hiện tại. Chương 4 ghi code minh hoạ cần đối chiếu. Không dùng để suy ra checkpoint thực tế. |
| `image_captioning.ipynb` | Code gần như `img-cap.ipynb`, chỉ khác epochs 20 thay 12 và freeze 2 thay 4; không có output text. Không nhầm với VQA. |
| `Mo_hinh_Image_Captioning_Flickr30k_Vietnamese.docx` | Giải thích captioning song ngữ, 49 visual tokens, ResNet50 + decoder mới, XLM-R + `<vi>/<en>/<BOS>/<EOS>`. Không phải cấu hình scratch VQA đang nạp. |
| `Phan_cong_BE_va_hop_dong_API_FEPYTHON.docx` | Hợp đồng triển khai chính: sync adapter, str answer, AppError, lazy AI imports, CPU mặc định, offline startup, artifacts, quản lý quyền sở hữu ảnh, phân chia file. |

## Thông tin xác nhận được từ output notebook scratch

Đây là **output đã có sẵn trong notebook**, không phải kết quả chạy lại trong lần bàn giao:

- Transformers 4.46.3; Tesla T4 15.6 GB VRAM.
- `d_model=768`, visual tokens 16, tổng 270,026,304 tham số.
- Đã chạy 5 epochs, checkpoint tốt nhất epoch 5, val loss 0.9037.
- Checkpoint `best_vqa_model.pt` được liệt kê khoảng 1080.9 MB, nhưng không đính kèm.
- Eval 20,418 QA dùng context prefix: EM 0.0922; token F1 0.4729; ROUGE-L 0.5182; BLEU 20.93 (thang sacrebleu).
- Ví dụ infer question-only cuối notebook sai so với ground truth “Xe bò”.

Không dùng các con số trên làm benchmark của adapter mới. Metric eval có metadata và câu hỏi question-only không cùng điều kiện. Notebook cũng có metric khác với Vintern; không so BLEU trực tiếp khi một bên dùng sacrebleu và bên kia nltk mà chưa chuẩn hoá cách tính.

## Các khác biệt cần báo lại nhóm

1. Báo cáo PDF/nhãn Gradio chưa cập nhật kiến trúc hiện tại. Nếu yêu cầu môn bắt buộc Transformer train from scratch, bản ViT5 không chứng minh đáp ứng điều đó; nhóm cần xác nhận đúng model được chọn. Không thể đổi kiến trúc loader mà vẫn nạp cùng trọng số.
2. Metadata dùng khi train/eval không có trong API. Chỉ nối preprocessing hiện tại không bảo đảm chất lượng demo.
3. Ba môi trường Transformers khác nhau; không có source BE để xác nhận môi trường và AppError/base. Không nên ép nâng toàn bộ môi trường sang v5 hay đưa monkey-patch Vintern vào scratch.
4. Báo cáo PDF ghi môn Lập trình Python và vẫn còn các chỗ điền tên/số liệu; người dùng đang gọi bài tập lớn AI. Đây là điểm chỉnh tài liệu của nhóm, không làm thay đổi hợp đồng adapter.
5. Gói tải lên không có trọng số, tokenizer, local model config, generation config hoặc bộ ảnh kiểm chứng độc lập.

## Phạm vi thay đổi

Giữ nguyên tất cả 13 file nguồn. Gói bàn giao là phần code mới phục vụ người 5; không chỉnh notebook huấn luyện, không tự train, không sửa báo cáo/Gradio/adapter Vintern hoặc các file chung thuộc thành viên khác.
