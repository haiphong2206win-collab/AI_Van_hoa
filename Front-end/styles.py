def get_css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
/* Giao diện tối kiểu You.com: sidebar trái, thẻ gợi ý, chọn mô hình dạng pill */
:root {
    --bg:#1f1f1f; --side:#171717; --card:#1a1a1a; --surface:#2a2a2a; --hover:#303030;
    --ink:#ececec; --muted:#8e8e8e; --line:#333333;
    --accent:#4f8cff; --accent-soft:rgba(79,140,255,.16);
}

html, body, .stApp, .stApp p, .stApp div, .stApp button, .stApp textarea, .stApp input, .stApp h1, .stApp h2, .stApp h3, .stApp li {
    font-family:'Inter', sans-serif;
}
[data-testid="stIconMaterial"] {font-family:'Material Symbols Rounded' !important;}
.stApp {background:var(--bg); color:var(--ink);}

/* Header Streamlit: giữ trong suốt để còn nút mở sidebar, ẩn menu/deploy */
[data-testid="stHeader"] {background:transparent;}
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stDecoration"] {display:none;}

.main .block-container, [data-testid="stMainBlockContainer"] {
    max-width:1100px; padding-top:3rem; padding-bottom:190px;
}

/* ───── Sidebar ───── */
[data-testid="stSidebar"] {background:var(--side); border-right:1px solid #232323;}
[data-testid="stSidebarUserContent"] {padding-top:0;}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {gap:.6rem;}
.logo {display:flex; align-items:center; gap:8px; margin-bottom:.6rem;}
.logo-mark {font-size:1.3rem;}
.logo-text {font-size:1.35rem; font-weight:700; letter-spacing:-.02em; color:var(--accent);}
.logo-text span {color:var(--ink); margin-left:2px; font-weight:600;}

.st-key-new_chat button {
    justify-content:flex-start; background:transparent; border:1px solid var(--line);
    border-radius:10px; color:var(--ink); font-size:.86rem; font-weight:500; min-height:40px;
}
.st-key-new_chat button:hover {background:var(--hover); border-color:var(--line); color:var(--ink);}

.side-label {font-size:.72rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; margin:1rem 0 .4rem;}
.hist-item {
    font-size:.84rem; color:#cfcfcf; padding:7px 10px; border-radius:8px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.hist-item:hover {background:var(--hover);}

/* ───── Màn hình chào ───── */
.welcome {padding-top:14vh;}
.welcome h1 {
    font-size:1.75rem !important; font-weight:600 !important; color:var(--muted) !important;
    padding:0; margin:0 0 1.8rem; letter-spacing:-.01em;
}
.welcome h1 span {color:inherit !important;}
.welcome h1 .hl {color:var(--accent) !important; font-weight:inherit;}
.cards {display:grid; grid-template-columns:1fr 1fr; gap:16px;}
.col-label {font-size:.86rem; color:var(--muted); margin-bottom:10px;}
.card {
    display:flex; align-items:center; gap:14px; margin-bottom:12px;
    background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px;
    transition:background .15s;
}
.card:hover {background:#242424;}
.thumb {
    width:48px; height:48px; border-radius:8px; flex-shrink:0; font-size:1.5rem;
    display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg, #2d3a55, #3a2d45);
}
.card-title {font-size:.88rem; font-weight:500; color:var(--ink); line-height:1.35;}
.card-sub {font-size:.75rem; color:var(--muted); margin-top:3px;}
@media (max-width:640px) {.cards {grid-template-columns:1fr;}}

/* ───── Tin nhắn ───── */
[data-testid="stElementContainer"]:has(.msg-user),
[data-testid="stElementContainer"]:has(.msg-bot) {display:none;}

[data-testid="stChatMessage"] {
    background:transparent !important; padding:0; margin-bottom:28px; gap:14px; align-items:flex-start;
}
[data-testid="stChatMessageContent"] {
    margin:0 !important; min-width:0; line-height:1.7; font-size:.97rem;
    background:transparent; border:none; padding:0;
}
[data-testid="stChatMessageContent"] [data-testid="stVerticalBlock"] {gap:.5rem;}
[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] p {margin:0 0 .75rem;}
[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] p:last-child {margin-bottom:0;}
[data-testid="stChatMessageContent"] img {border-radius:14px;}

/* AI: chữ trải rộng, không bong bóng */
[data-testid="stChatMessage"]:has(.msg-bot) [data-testid="stChatMessageContent"] {flex:1 1 auto; padding-top:4px;}
[data-testid="stChatMessage"]:has(.msg-bot) > :first-child {
    width:30px; height:30px; border-radius:50% !important;
    background:var(--accent-soft) !important; border:none !important;
}
[data-testid="stChatMessage"]:has(.msg-bot) > :first-child * {color:var(--accent) !important;}

/* Người dùng: ẩn avatar, bong bóng bên phải */
[data-testid="stChatMessage"]:has(.msg-user) > :first-child {display:none !important;}
[data-testid="stChatMessage"]:has(.msg-user) {justify-content:flex-end;}
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] {flex:0 1 auto; max-width:75%;}
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stVerticalBlock"] {align-items:flex-end;}
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stElementContainer"] {width:auto !important;}
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stMarkdownContainer"] {
    background:var(--surface); border-radius:18px; padding:9px 16px;
}

.model-chip {display:block; width:fit-content; font-size:.75rem; font-weight:500; color:var(--muted);}

[data-testid="stSpinner"] {color:var(--muted); font-style:italic;}
[data-testid="stSpinner"] i, [data-testid="stSpinner"] > div > div:first-child {border-top-color:var(--accent) !important;}

/* ───── Thanh đáy ───── */
[data-testid="stBottom"] > div {background:var(--bg);}
[data-testid="stBottomBlockContainer"] {background:transparent; max-width:1100px; padding-top:.6rem; padding-bottom:1.4rem;}
[data-testid="stBottomBlockContainer"] > [data-testid="stVerticalBlock"] {gap:.6rem;}

/* Chip "Ảnh đang sử dụng" */
.st-key-image_chip {background:var(--card); border:1px solid var(--line); border-radius:12px; padding:6px 10px;}
.st-key-image_chip img {border-radius:6px; object-fit:cover;}
.chip-title {font-size:.82rem; font-weight:500; color:var(--ink); line-height:1.35;}
.chip-sub {font-size:.74rem; color:var(--muted); line-height:1.35;}
.st-key-clear_img button {
    border-radius:50%; width:28px; height:28px; min-height:28px; padding:0;
    border:none; background:transparent; color:var(--muted);
}
.st-key-clear_img button:hover {background:var(--hover); color:var(--ink);}

/* Chọn mô hình dạng pill, căn giữa */
.st-key-model_bar [data-testid="stButtonGroup"] > div {justify-content:center; gap:8px;}
.st-key-model_bar button {
    background:transparent; border:1px solid var(--line); border-radius:8px;
    color:#d0d0d0; font-size:.8rem; font-weight:500; min-height:30px; padding:2px 12px;
}
.st-key-model_bar button:hover {background:var(--hover); border-color:var(--line); color:var(--ink);}
.st-key-model_bar button[data-testid="stBaseButton-pillsActive"] {
    background:var(--accent-soft); border-color:transparent; color:var(--accent);
}

/* Ô nhập */
[data-testid="stChatInput"] {
    border-radius:12px !important; border:1px solid var(--line) !important;
    background:var(--surface) !important; box-shadow:none;
}
[data-testid="stChatInput"]:focus-within {border-color:#4a4a4a !important;}
[data-testid="stChatInput"] textarea {background:transparent !important; color:var(--ink) !important; font-size:.95rem;}
[data-testid="stChatInputSubmitButton"] {
    background:#d0d0d0 !important; color:#1f1f1f !important; border-radius:50% !important;
}
[data-testid="stChatInputSubmitButton"]:disabled {background:#444 !important; color:#888 !important;}
</style>
"""
