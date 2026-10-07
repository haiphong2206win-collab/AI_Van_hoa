def get_css():
    return """
<style>
header {visibility: hidden;}
.stApp {background:#f8fafc; color:#1e293b;}
.main .block-container {max-width:900px; padding-top:6rem; padding-bottom:140px;}

/* Thanh header ghim cố định trên cùng */
.st-key-topbar {
    position:fixed; top:0; left:0; width:100%; z-index:1000;
    box-sizing:border-box; background:#f8fafc;
    padding:12px max(1rem, calc((100vw - 900px) / 2 + 1rem));
    border-bottom:1px solid #e2e8f0;
}

/* Header */
.logo {font-size:1.5rem; font-weight:700; color:#1e3a8a; line-height:2.4rem;}
.logo span {color:#2563eb;}
button[kind="primary"], button[data-testid="stBaseButton-primary"] {
    background:#2563eb; border:none; border-radius:8px; color:#fff; font-weight:500;
}
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {background:#1d4ed8;}

/* Tin nhắn */
[data-testid="stChatMessage"] {background:transparent; padding:0; margin-bottom:14px; gap:12px; align-items:flex-start;}
[data-testid="stChatMessageContent"] {
    width:fit-content; max-width:75%;
    background:#ffffff; border:1px solid #e2e8f0;
    border-radius:14px; padding:12px 16px;
}
/* Avatar (ô đầu tiên của mỗi tin nhắn) */
[data-testid="stChatMessage"]:has(.msg-bot) > :first-child {background:#2563eb !important; color:#fff !important; border:none !important;}
[data-testid="stChatMessage"]:has(.msg-user) > :first-child {background:#dbeafe !important; color:#2563eb !important; border:none !important;}
.msg-user, .msg-bot {display:none;}

/* Người dùng: bên phải (avatar nằm ngoài cùng bên phải) */
[data-testid="stChatMessage"]:has(.msg-user) {flex-direction:row-reverse !important;}
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] {
    background:#eaf3ff; border-color:#cfe3ff;
}

/* Chatbot: bên trái (mặc định) */

/* Nhãn mô hình */
.model-chip {
    display:inline-block; font-size:.72rem; font-weight:500; color:#475569;
    background:#e8eef6; border-radius:6px; padding:2px 8px; margin-bottom:6px;
}
</style>
"""
