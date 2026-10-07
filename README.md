# VietCulture AI - Frontend

Đây là thư mục chứa mã nguồn Frontend cho dự án VietCulture AI, được xây dựng bằng [Streamlit](https://streamlit.io/).

## Yêu cầu hệ thống
- Python 3.8 trở lên
- Trình duyệt web hiện đại (Chrome, Edge, Firefox,...)

## Hướng dẫn cài đặt và chạy (trên Windows PowerShell)

### Bước 1: Mở Terminal (PowerShell)
Điều hướng đến đúng thư mục chứa source code Frontend:
```powershell
cd "D:\Documents\python\VietCulture AI\AI_Van_hoa_FE\Front-end"
```

### Bước 2: Tạo môi trường ảo (Tùy chọn nhưng khuyên dùng)
Tạo môi trường ảo để các thư viện không bị xung đột với các dự án khác:
```powershell
python -m venv venv
```
Kích hoạt môi trường ảo:
```powershell
.\venv\Scripts\Activate
```
*(Nếu gặp lỗi "cannot be loaded because running scripts is disabled on this system", hãy chạy lệnh `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` trước, sau đó kích hoạt lại).*

### Bước 3: Cài đặt thư viện
Cài đặt các thư viện bắt buộc bao gồm `streamlit`, `requests`, và `python-dotenv`:
```powershell
pip install -r requirements.txt
```
*(Nếu bạn chưa tạo file requirements.txt, có thể chạy lệnh: `pip install streamlit>=1.43 requests python-dotenv`)*

### Bước 4: Thiết lập biến môi trường
Dự án sử dụng các biến môi trường để cấu hình URL của Backend.
- Copy file `.env.example` thành file `.env`:
```powershell
cp .env.example .env
```
- Mở file `.env` và kiểm tra lại `API_BASE_URL` cho đúng với địa chỉ Backend của bạn (mặc định là `http://127.0.0.1:8000/api/v1`).

### Bước 5: Chạy ứng dụng
Khởi chạy Frontend bằng lệnh của Streamlit:
```powershell
streamlit run app.py
```
Sau khi chạy thành công, Terminal sẽ hiển thị địa chỉ local (thường là `http://localhost:8501`). Trình duyệt của bạn sẽ tự động mở trang web lên.

---
**Lưu ý:** Hãy đảm bảo rằng Backend (API) đang được chạy song song để Frontend có thể gọi và xử lý suy luận (hiện tại backend mặc định kết nối tại `http://127.0.0.1:8000`).
