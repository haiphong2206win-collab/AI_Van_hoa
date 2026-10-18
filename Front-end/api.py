import requests
import streamlit as st
from config import API_BASE_URL

@st.cache_data(ttl=60)
def fetch_models():
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=5)
        if response.status_code == 200:
            return response.json().get("models", [])
    except:
        pass
    # Mặc định theo hợp đồng nếu BE chưa bật
    return [
        {"id": "scratch", "name": "Model tự xây", "available": True, "load_state": "unloaded"},
        {"id": "finetuned", "name": "Model fine tune", "available": False, "load_state": "error"}
    ]

def generate_reply(model_id: str, prompt: str, image_bytes) -> str:
    """Gọi API suy luận thực tế tới Backend."""
    if not image_bytes:
        return "⚠️ Vui lòng cung cấp một bức ảnh để AI phân tích."
    
    try:
        # Giả định ảnh được tải lên từ st.chat_input
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {
            "question": prompt.strip() if prompt else "",
            "model_id": model_id
        }
        
        response = requests.post(f"{API_BASE_URL}/predict", files=files, data=data, timeout=190)
        
        if response.status_code == 200:
            return response.json().get("answer", "Không có câu trả lời.")
            
        # Xử lý lỗi theo hợp đồng HTTP
        try:
            error_msg = response.json().get("error", {}).get("message", "Lỗi không xác định")
        except:
            error_msg = response.text
            
        if response.status_code == 413:
            return "❌ Lỗi: Ảnh quá lớn (tối đa 10MB)."
        elif response.status_code == 415:
            return "❌ Lỗi: Định dạng ảnh không hợp lệ."
        elif response.status_code == 422:
            return f"❌ Lỗi dữ liệu (422): {error_msg}"
        elif response.status_code == 503:
            return f"❌ Dịch vụ không khả dụng (503): {error_msg}"
        elif response.status_code == 504:
            return "⏱️ Lỗi: Quá thời gian suy luận của AI (timeout)."
        else:
            return f"❌ Lỗi hệ thống ({response.status_code}): {error_msg}"
            
    except requests.exceptions.Timeout:
        return "⏱️ Lỗi: Mất kết nối, quá thời gian chờ phản hồi từ Backend."
    except requests.exceptions.ConnectionError:
        return "❌ Lỗi: Không thể kết nối đến Backend. Hãy chắc chắn Backend đang chạy tại http://127.0.0.1:8000."
    except Exception as e:
        return f"❌ Lỗi không xác định: {str(e)}"
