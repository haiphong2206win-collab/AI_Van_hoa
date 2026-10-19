import html

import streamlit as st
from config import API_BASE_URL
from api import fetch_models, generate_reply
from styles import get_css
from state import init_session_state, new_chat, clear_image

# Cần Streamlit >= 1.43 (st.chat_input hỗ trợ accept_file, st.pills)
st.set_page_config(page_title="VietCulture AI", page_icon="🏛️", layout="wide",
                   initial_sidebar_state="expanded")

# Câu hỏi FE tự gửi khi người dùng chỉ gửi ảnh, không nhập text (BE bắt buộc có question)
DEFAULT_QUESTION = "Đây là món ăn gì? Nguyên liệu gồm những gì và cách nấu như thế nào?"

# Áp dụng CSS
st.markdown(get_css(), unsafe_allow_html=True)

# Khởi tạo state
init_session_state()

# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="logo"><span class="logo-mark">🏛️</span>'
        '<span class="logo-text">VietCulture<span>AI</span></span></div>',
        unsafe_allow_html=True,
    )
    st.button("⊕  Cuộc trò chuyện mới", key="new_chat",
              use_container_width=True, on_click=new_chat)

    questions = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    if questions:
        items = "".join(f'<div class="hist-item">{html.escape(q)}</div>' for q in questions)
        st.markdown(f'<div class="side-label">Cuộc trò chuyện này</div>{items}',
                    unsafe_allow_html=True)

# ───────────────────────── Danh sách mô hình ─────────────────────────
models_data = fetch_models()
options = [
    {"id": m["id"], "name": m["name"], "available": m.get("available")}
    for m in models_data
]

# ───────────────────────── Màn hình chào (chưa có tin nhắn) ─────────────────────────
def card(icon, title, sub):
    return (f'<div class="card"><div class="thumb">{icon}</div>'
            f'<div><div class="card-title">{title}</div><div class="card-sub">{sub}</div></div></div>')

if not st.session_state.messages and not st.session_state.get("pending"):
    st.markdown(
        f"""
<div class="welcome">
  <h1>Hỏi <b class="hl">VietCulture AI</b> về món ăn Việt</h1>
  <div class="cards">
    <div class="col">
      <div class="col-label">Bắt đầu</div>
      {card("📷", "Gửi ảnh món ăn", "Bấm dấu ＋ trong ô nhập · JPG, PNG, WEBP")}
      {card("💬", "Đặt câu hỏi hoặc để trống", "AI sẽ tự nhận diện món ăn")}
    </div>
    <div class="col">
      <div class="col-label">Gợi ý câu hỏi</div>
      {card("🍜", "Món này có nguồn gốc từ đâu?", "Văn hoá")}
      {card("🥢", "Nguyên liệu và cách nấu thế nào?", "Công thức")}
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# ───────────────────────── Lịch sử chat ─────────────────────────
for m in st.session_state.messages:
    if m["role"] == "user":
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown('<span class="msg-user"></span>', unsafe_allow_html=True)
            if m.get("image"):
                st.image(m["image"], width=300)
            st.markdown(m["content"])
    else:
        with st.chat_message("assistant", avatar=":material/auto_awesome:"):
            st.markdown('<span class="msg-bot"></span>', unsafe_allow_html=True)
            st.markdown(f'<span class="model-chip">{m["model"]}</span>', unsafe_allow_html=True)
            st.markdown(m["content"])

# ───────────────────────── Đang chờ AI trả lời ─────────────────────────
# Câu hỏi đã hiện ở trên (lượt chạy trước), giờ mới gọi API và hiện "AI đang suy nghĩ..."
pending = st.session_state.get("pending")
if pending:
    with st.chat_message("assistant", avatar=":material/auto_awesome:"):
        st.markdown('<span class="msg-bot"></span>', unsafe_allow_html=True)
        st.markdown(f'<span class="model-chip">{pending["model_name"]}</span>', unsafe_allow_html=True)
        with st.spinner("AI đang suy nghĩ..."):
            reply = generate_reply(pending["model_id"], pending["question"], pending["image"])
    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "model": pending["model_name"]}
    )
    st.session_state.pending = None
    st.rerun()

# ───────────────────────── Thanh đáy: ảnh đang dùng + chọn mô hình ─────────────────────────
# st.bottom: vùng ghim đáy trang của Streamlit, đặt ngay trên ô nhập
with st.bottom:
    if st.session_state.current_image:
        with st.container(key="image_chip"):
            c1, c2, c3 = st.columns([1, 12, 1], vertical_alignment="center", gap="small")
            c1.image(st.session_state.current_image, width=40)
            c2.markdown(
                '<div class="chip-title">Ảnh đang sử dụng</div>'
                '<div class="chip-sub">Hỏi tiếp về ảnh này mà không cần gửi lại</div>',
                unsafe_allow_html=True,
            )
            c3.button("✕", key="clear_img", on_click=clear_image, help="Bỏ ảnh này")

    with st.container(key="model_bar"):
        # st.pills dùng id (chuỗi) làm option; truyền dict sẽ bị hiểu nhầm default là danh sách khoá
        by_id = {o["id"]: o for o in options}
        default_id = next((o["id"] for o in options if o["available"]), next(iter(by_id), None))
        picked_id = st.pills(
            "Mô hình", list(by_id),
            default=default_id,
            format_func=lambda i: by_id[i]["name"] if by_id[i]["available"] else f'{by_id[i]["name"]} · offline',
            label_visibility="collapsed",
            key="model_pick",
        )
    selected_option = by_id.get(picked_id or default_id)
    selected_model_id = selected_option["id"] if selected_option else "scratch"
    selected_model_name = selected_option["name"] if selected_option else "Model tự xây"

# ───────────────────────── Ô nhập (tự ghim đáy trang) ─────────────────────────
# accept_file=True => có nút ＋ để đính kèm ảnh và xem trước ảnh ngay trong ô nhập
# Người dùng có thể gửi: ảnh + câu hỏi, chỉ ảnh, hoặc chỉ câu hỏi (hỏi tiếp về ảnh đang dùng)
submitted = st.chat_input(
    "Hỏi bất cứ điều gì về món ăn trong ảnh...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
    max_chars=2000,  # Khớp giới hạn độ dài câu hỏi của BE
)

if submitted:
    text = (submitted.text or "").strip()
    new_img = submitted.files[0].getvalue() if submitted.files else None

    if new_img:
        st.session_state.current_image = new_img

    if text or new_img:
        st.session_state.messages.append(
            {"role": "user", "content": text or "(đã gửi ảnh)", "image": new_img}
        )
        # Chỉ nhập text thì dùng lại ảnh đang sử dụng; BE bắt buộc phải có ảnh
        image_to_send = new_img or st.session_state.current_image

        reply = None
        if not image_to_send:
            reply = "⚠️ Vui lòng gửi kèm một bức ảnh (bấm ＋) để AI trả lời câu hỏi của bạn."
        # Nếu model không khả dụng, cảnh báo
        elif selected_option and not selected_option["available"]:
            reply = f"⚠️ Mô hình '{selected_model_name}' hiện không khả dụng. Xin vui lòng chọn mô hình khác."
        else:
            # Chưa gọi API ở đây: rerun để câu hỏi hiện ngay, lượt sau mới gọi AI
            # Có text thì gửi đúng câu hỏi người dùng, không có thì dùng câu hỏi mặc định
            st.session_state.pending = {
                "question": text or DEFAULT_QUESTION,
                "image": image_to_send,
                "model_id": selected_model_id,
                "model_name": selected_model_name,
            }

        if reply:
            st.session_state.messages.append(
                {"role": "assistant", "content": reply, "model": selected_model_name}
            )
        st.rerun()
