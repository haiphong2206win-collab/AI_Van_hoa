import streamlit as st
from config import API_BASE_URL
from api import fetch_models, generate_reply
from styles import get_css
from state import init_session_state, new_chat, clear_image

# Cần Streamlit >= 1.43 (st.chat_input hỗ trợ accept_file)
st.set_page_config(page_title="VietCulture AI", page_icon="🏛️", layout="wide")

# Áp dụng CSS
st.markdown(get_css(), unsafe_allow_html=True)

# Khởi tạo state
init_session_state()

# ───────────────────────── Header ─────────────────────────
with st.container(key="topbar"):
    c_logo, c_model, c_new = st.columns([5, 3, 3], vertical_alignment="center")
    with c_logo:
        st.markdown('<div class="logo">🏛️ VietCulture <span>AI</span></div>', unsafe_allow_html=True)
    with c_model:
        models_data = fetch_models()
        # Tạo danh sách hiển thị
        options = []
        for m in models_data:
            status = "" if m.get("available") else f" (Không khả dụng - {m.get('load_state', 'unloaded')})"
            options.append({"id": m["id"], "name": m["name"], "label": f"{m['name']}{status}", "available": m.get("available")})
            
        selected_option = st.selectbox(
            "Mô hình", options,
            format_func=lambda x: f"Mô hình: {x['label']}",
            label_visibility="collapsed",
        )
        selected_model_id = selected_option["id"] if selected_option else "scratch"
        selected_model_name = selected_option["name"] if selected_option else "Model tự xây"
    with c_new:
        st.button("＋ Cuộc trò chuyện mới", type="primary",
                  use_container_width=True, on_click=new_chat)

# ───────────────────────── Lịch sử chat ─────────────────────────
for m in st.session_state.messages:
    if m["role"] == "user":
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown('<span class="msg-user"></span>', unsafe_allow_html=True)
            if m.get("image"):
                st.image(m["image"], width=300)
            st.markdown(m["content"])
    else:
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            st.markdown('<span class="msg-bot"></span>', unsafe_allow_html=True)
            st.markdown(f'<span class="model-chip">{m["model"]}</span>', unsafe_allow_html=True)
            st.markdown(m["content"])

# ───────────────────────── Chip "Ảnh đang sử dụng" ─────────────────────────
if st.session_state.current_image:
    with st.container(border=True): 
        c1, c2, c3 = st.columns([1, 8, 1], vertical_alignment="center")
        c1.image(st.session_state.current_image, width=48)
        c2.caption("Ảnh đang sử dụng")
        c3.button("✕", key="clear_img", on_click=clear_image)

# ───────────────────────── Ô nhập (tự ghim đáy trang) ─────────────────────────
# accept_file=True => có nút kẹp giấy 📎 và xem trước ảnh ngay trong ô nhập
submitted = st.chat_input(
    "Nhập câu hỏi về ảnh...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if submitted:
    text = submitted.text or ""
    new_img = submitted.files[0].getvalue() if submitted.files else None

    if new_img:
        st.session_state.current_image = new_img

    if text or new_img:
        st.session_state.messages.append(
            {"role": "user", "content": text or "(đã gửi ảnh)", "image": new_img}
        )
        # Nếu model không khả dụng, cảnh báo
        if selected_option and not selected_option["available"]:
            reply = f"⚠️ Mô hình '{selected_model_name}' hiện không khả dụng. Xin vui lòng chọn mô hình khác."
        else:
            reply = generate_reply(selected_model_id, text, st.session_state.current_image)
            
        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "model": selected_model_name}
        )
        st.rerun()