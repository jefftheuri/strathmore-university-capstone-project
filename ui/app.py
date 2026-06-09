"""
ui/app.py  –  SureRide WhatsApp-style chat
Uses st.components.v1.html() for the chat area so our CSS is never
stripped or overridden by Streamlit's own stylesheet.
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from langgraph_agent.agent import run_turn, new_state

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SureRide",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# view will be set via tabs — define a placeholder so CSS injection below works
view = ""  # resolved after tabs are created

# ── Global page CSS (always injected — covers both tab views) ─────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Tab styles ── */
[data-testid="stTabs"] [data-testid="stTab"] {
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #f0f4f0 !important; }
section[data-testid="stSidebar"] .stMarkdown { color: #333 !important; }

.zone-pill {
    display: inline-block;
    background: rgba(37,211,102,.12);
    border: 1px solid rgba(37,211,102,.3);
    color: #0a7a41; border-radius: 12px;
    padding: 3px 10px; font-size: 11.5px;
    font-weight: 500; margin: 2px;
}

/* ── Fare / payment / confirmed cards (chat tab) ── */
.fare-card, .payment-card, .confirmed-card {
    border-radius: 14px; padding: 16px 18px;
    margin: 6px 0 10px;
}
.fare-card {
    background: linear-gradient(135deg,#1a3a2a,#0f3d2a);
    border: 1px solid rgba(37,211,102,.25);
    box-shadow: 0 3px 16px rgba(0,0,0,.25);
}
.payment-card {
    background: linear-gradient(135deg,#1a1a3a,#0d1f3d);
    border: 1px solid rgba(100,130,255,.3);
    box-shadow: 0 3px 16px rgba(0,0,0,.25);
}
.confirmed-card {
    background: linear-gradient(135deg,#128C7E,#25D366);
    box-shadow: 0 4px 20px rgba(37,211,102,.3);
}

/* ── Dashboard metric cards ── */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin-bottom: 1rem;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0.2rem 0;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.85rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

/* ── Chat tab — center a narrow column ── */
.chat-tab-wrap {
    background: #efeae2;
    border-radius: 12px;
    overflow: hidden;
    max-width: 520px;
    margin: 0 auto;
}

/* ── Dashboard tab background ── */
.dash-tab-wrap {
    background: #0d1117;
    color: #c9d1d9;
    border-radius: 12px;
    padding: 1.5rem;
    min-height: 500px;
}
.dash-tab-wrap h3, .dash-tab-wrap h4 {
    color: #e6edf3 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 24px !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    font-size: 14px !important;
    transition: all .15s !important;
    border: none !important;
}

/* Chat input styling */
[data-testid="stBottom"] {
    background: #f0f2f5 !important;
    border-top: 1px solid #e9edef !important;
    padding: 8px 12px !important;
}
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    border-radius: 24px !important;
    border: none !important;
    font-size: 15px !important;
    padding: 10px 18px !important;
    color: #111 !important;
}

/* ── Phone frame for chat tab ── */
.phone-scene {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 30px 0 20px;
    min-height: 820px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    margin: 0 auto;
}
.phone-frame {
    position: relative;
    width: 390px;
    min-height: 760px;
    background: #efeae2;
    border-radius: 50px;
    box-shadow:
        0 0 0 2px #333,
        0 0 0 6px #555,
        0 0 0 8px #222,
        0 50px 100px rgba(0,0,0,0.7);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
/* Notch */
.phone-frame::before {
    content: '';
    position: absolute;
    top: 0; left: 50%; transform: translateX(-50%);
    width: 130px; height: 30px;
    background: #111;
    border-radius: 0 0 22px 22px;
    z-index: 100;
}
/* Side buttons */
.phone-frame::after {
    content: '';
    position: absolute;
    top: 100px; right: -10px;
    width: 4px; height: 60px;
    background: #444;
    border-radius: 2px;
    box-shadow: 0 80px 0 #444;
}
.phone-vol-btn {
    position: absolute;
    top: 120px; left: -6px;
    width: 4px; height: 40px;
    background: #444;
    border-radius: 2px;
    box-shadow: 0 56px 0 #444, 0 104px 0 #444;
    z-index: 10;
}
.phone-inner {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    border-radius: 44px;
}
.phone-status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 38px 22px 4px;
    background: #008069;
    font-size: 11px;
    font-weight: 600;
    color: white;
    font-family: -apple-system, sans-serif;
    flex-shrink: 0;
}
.phone-chat-area {
    flex: 1;
    overflow-y: auto;
    background: #efeae2;
}
.phone-input-bar {
    background: #f0f2f5;
    border-top: 1px solid #e9edef;
    padding: 8px 12px;
    flex-shrink: 0;
    min-height: 56px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.phone-input-bar input {
    flex: 1;
    background: white;
    border: none;
    border-radius: 22px;
    padding: 9px 16px;
    font-size: 15px;
    outline: none;
    color: #333;
}
.phone-input-bar .mic-btn {
    width: 40px; height: 40px;
    background: #25D366;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; cursor: pointer; border: none;
    box-shadow: 0 2px 8px rgba(37,211,102,0.4);
}

/* Constrain Streamlit content to phone width */
[data-testid="stTabsContent"]:first-child {
    padding: 0 !important;
    max-width: 100% !important;
    background: transparent !important;
}
[data-testid="stTabsContent"]:first-child .stChatInput {
    max-width: 366px;
    border-radius: 22px;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def now_time() -> str:
    return datetime.now().strftime("%H:%M")

def md_to_html(text: str) -> str:
    """Convert *bold* and [link](url) markdown to HTML, preserve newlines."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<b>\1</b>', text)
    text = re.sub(r'_(.+?)_',       r'<em>\1</em>', text)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank" style="color:#128C7E;font-weight:600;">\1</a>',
        text,
    )
    text = text.replace('\n', '<br>')
    return text


# ── Chat renderer (rendered in st.iframe so Streamlit CSS cannot interfere) ──────────
_CHAT_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body {
    font-family: -apple-system, 'Segoe UI', 'Inter', sans-serif;
    background: #efeae2;
    font-size: 15px;
}
.chat-wrap { padding: 8px 10px 4px; }
.day-chip {
    text-align: center; margin: 6px 0 10px;
}
.day-chip span {
    background: rgba(255,255,255,.78);
    color: #54656f; font-size: 12px;
    padding: 4px 12px; border-radius: 7px;
    box-shadow: 0 1px 1px rgba(0,0,0,.08);
}

/* ── Message rows ── */
.msg-row { display: flex; margin: 2px 0 1px; align-items: flex-end; }
.msg-row-bot  { justify-content: flex-start; padding-right: 60px; }
.msg-row-user { justify-content: flex-end;   padding-left:  60px; }

/* ── Bubbles ── */
.bubble {
    position: relative;
    max-width: 100%;
    padding: 6px 7px 8px 9px;
    font-size: 14.5px;
    line-height: 1.55;
    color: #111;
    word-break: break-word;
}
.bubble-bot {
    background: #ffffff;
    border-radius: 0 7.5px 7.5px 7.5px;
    box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
}
.bubble-user {
    background: #d9fdd3;
    border-radius: 7.5px 0 7.5px 7.5px;
    box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
}

/* WhatsApp tail on bot bubble */
.bubble-bot::before {
    content: '';
    position: absolute;
    top: 0; left: -8px;
    width: 0; height: 0;
    border-top: 8px solid #ffffff;
    border-left: 8px solid transparent;
}

/* WhatsApp tail on user bubble */
.bubble-user::before {
    content: '';
    position: absolute;
    top: 0; right: -8px;
    width: 0; height: 0;
    border-top: 8px solid #d9fdd3;
    border-right: 8px solid transparent;
}

/* ── Timestamp inside bubble ── */
.msg-meta {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 3px;
    margin-top: 2px;
    height: 15px;
}
.msg-time {
    font-size: 11px;
    color: #667781;
    white-space: nowrap;
}
.tick { font-size: 14px; color: #53bdeb; line-height: 1; }

b   { font-weight: 600; }
em  { font-style: italic; color: #555; }
a   { color: #128C7E; font-weight: 600; }
"""

def _build_phone_html(messages: list) -> str:
    """Build a complete phone-frame WhatsApp UI as a self-contained HTML document."""
    date_str = datetime.now().strftime("%A, %d %B %Y")
    now_str  = datetime.now().strftime("%H:%M")

    bubbles = ""
    for msg in messages:
        html_text = md_to_html(msg["text"])
        ts        = msg["time"]
        if msg["role"] == "bot":
            bubbles += f"""
<div class="msg-row msg-row-bot">
  <div class="bubble bubble-bot">
    <span class="msg-text">{html_text}</span>
    <div class="msg-meta"><span class="msg-time">{ts}</span></div>
  </div>
</div>"""
        else:
            bubbles += f"""
<div class="msg-row msg-row-user">
  <div class="bubble bubble-user">
    <span class="msg-text">{html_text}</span>
    <div class="msg-meta">
      <span class="msg-time">{ts}</span>
      <span class="tick">✓✓</span>
    </div>
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
  font-family: -apple-system,'Segoe UI','Inter',sans-serif;
  background: linear-gradient(145deg,#0f0c29,#302b63,#24243e);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 24px 0 16px;
}}

/* Phone shell */
.phone {{
  position: relative;
  width: 370px;
  background: #efeae2;
  border-radius: 48px;
  box-shadow:
    0 0 0 2px #2a2a2a,
    0 0 0 5px #555,
    0 0 0 7px #1a1a1a,
    0 40px 80px rgba(0,0,0,.75);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 720px;
}}
/* Notch */
.phone::before {{
  content: '';
  position: absolute;
  top: 0; left: 50%; transform: translateX(-50%);
  width: 120px; height: 28px;
  background: #111;
  border-radius: 0 0 20px 20px;
  z-index: 50;
}}
/* Power button (right) */
.phone::after {{
  content: '';
  position: absolute;
  top: 110px; right: -6px;
  width: 4px; height: 55px;
  background: #3a3a3a;
  border-radius: 2px;
}}
/* Volume buttons (left) */
.vol-btns {{
  position: absolute;
  top: 100px; left: -6px;
  display: flex; flex-direction: column; gap: 12px;
  z-index: 10;
}}
.vol-btns span {{
  display: block;
  width: 4px; height: 34px;
  background: #3a3a3a;
  border-radius: 2px;
}}

/* Status bar */
.status-bar {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 32px 18px 2px;
  background: #008069;
  font-size: 11px; font-weight: 700; color: white;
  flex-shrink: 0;
}}
.status-right {{ display: flex; gap: 6px; align-items: center; }}

/* WhatsApp header */
.wa-header {{
  display: flex; align-items: center; gap: 10px;
  padding: 6px 12px 10px;
  background: #008069;
  flex-shrink: 0;
}}
.avatar {{
  width: 38px; height: 38px; border-radius: 50%;
  background: #25D366;
  display: flex; align-items: center; justify-content: center;
  font-size: 19px; flex-shrink: 0;
}}
.wa-info {{ flex: 1; }}
.wa-name   {{ font-size: 15px; font-weight: 600; color: white; }}
.wa-status {{ font-size: 11px; color: #b2dfdb; margin-top: 1px; }}
.wa-icons  {{ display: flex; gap: 16px; color: white; font-size: 19px; }}

/* Chat area */
.chat-area {{
  flex: 1;
  overflow-y: auto;
  background: #efeae2;
  padding: 6px 8px 4px;
}}
.day-chip {{ text-align: center; margin: 6px 0 10px; }}
.day-chip span {{
  background: rgba(255,255,255,.78);
  color: #54656f; font-size: 11.5px;
  padding: 3px 10px; border-radius: 7px;
  box-shadow: 0 1px 1px rgba(0,0,0,.08);
}}

/* Message rows */
.msg-row {{ display: flex; margin: 2px 0 1px; align-items: flex-end; }}
.msg-row-bot  {{ justify-content: flex-start; padding-right: 55px; }}
.msg-row-user {{ justify-content: flex-end;   padding-left:  55px; }}

/* Bubbles */
.bubble {{
  position: relative;
  max-width: 100%;
  padding: 6px 7px 8px 9px;
  font-size: 14px;
  line-height: 1.5;
  color: #111;
  word-break: break-word;
}}
.bubble-bot {{
  background: #ffffff;
  border-radius: 0 7.5px 7.5px 7.5px;
  box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
}}
.bubble-user {{
  background: #d9fdd3;
  border-radius: 7.5px 0 7.5px 7.5px;
  box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
}}
.bubble-bot::before {{
  content: '';
  position: absolute;
  top: 0; left: -8px;
  border-top: 8px solid #ffffff;
  border-left: 8px solid transparent;
}}
.bubble-user::before {{
  content: '';
  position: absolute;
  top: 0; right: -8px;
  border-top: 8px solid #d9fdd3;
  border-right: 8px solid transparent;
}}
.msg-meta {{
  display: flex; justify-content: flex-end;
  align-items: center; gap: 3px;
  margin-top: 2px; height: 14px;
}}
.msg-time {{ font-size: 10.5px; color: #667781; }}
.tick {{ font-size: 13px; color: #53bdeb; }}
b   {{ font-weight: 600; }}
em  {{ font-style: italic; color: #555; }}
a   {{ color: #128C7E; font-weight: 600; }}

/* Input bar */
.input-bar {{
  display: flex; align-items: center; gap: 8px;
  background: #f0f2f5;
  border-top: 1px solid #e9edef;
  padding: 7px 10px;
  flex-shrink: 0;
}}
.input-field {{
  flex: 1;
  background: white;
  border: none;
  border-radius: 22px;
  padding: 8px 14px;
  font-size: 14px;
  color: #aaa;
  font-family: inherit;
  cursor: default;
}}
.send-btn {{
  width: 38px; height: 38px;
  background: #25D366;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px;
  box-shadow: 0 2px 6px rgba(37,211,102,.4);
  flex-shrink: 0;
}}
</style></head>
<body>
<div class="phone">
  <div class="vol-btns"><span></span><span></span></div>

  <!-- Status bar -->
  <div class="status-bar">
    <span>{now_str}</span>
    <div class="status-right">
      <span>&#9679;&#9679;&#9679;&#9679;</span>
      <span>5G</span>
      <span>&#128267; 87%</span>
    </div>
  </div>

  <!-- WhatsApp header -->
  <div class="wa-header">
    <span style="color:white;font-size:20px;">&#8592;</span>
    <div class="avatar">&#x1F697;</div>
    <div class="wa-info">
      <div class="wa-name">SureRide</div>
      <div class="wa-status">&#x1F7E2; online</div>
    </div>
    <div class="wa-icons">
      <span>&#x1F4F9;</span>
      <span>&#x1F4DE;</span>
      <span>&#8942;</span>
    </div>
  </div>

  <!-- Chat messages -->
  <div class="chat-area" id="chat">
    <div class="day-chip"><span>{date_str}</span></div>
    {bubbles}
  </div>

  <!-- Input bar (display only — actual input is Streamlit widget below) -->
  <div class="input-bar">
    <div class="input-field">Type a message…</div>
    <div class="send-btn">&#x1F3A4;</div>
  </div>
</div>
<script>var c=document.getElementById('chat');c.scrollTop=c.scrollHeight;</script>
</body></html>"""


def render_chat(messages: list):
    # Height: phone frame + some breathing room
    h = min(max(len(messages) * 72 + 380, 580), 900)
    components.html(_build_phone_html(messages), height=h, scrolling=False)


# ── Card renderers ────────────────────────────────────────────────────────────
def render_fare_card(state: dict):
    from utils.pricing import calculate_fare
    dist  = state.get("distance_km", 0)
    fare  = state.get("fare_kes", 0)
    surge = state.get("surge_applied", False)
    f     = calculate_fare(dist)
    surge_html = '<span style="background:rgba(255,169,77,.2);color:#ffa94d;border:1px solid rgba(255,169,77,.3);border-radius:8px;padding:1px 8px;font-size:11px;font-weight:600;margin-left:6px;">⚡ Surge</span>' if surge else ""

    st.markdown(f"""
<div class="fare-card">
  <div style="color:#25D366;font-size:15px;font-weight:700;margin-bottom:12px;">🧾 Fare Breakdown {surge_html}</div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:rgba(255,255,255,.82);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.07);">
    <span>📏 Distance</span><span>{dist} km</span></div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:rgba(255,255,255,.82);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.07);">
    <span>🚦 Base fare</span><span>KES {f.base_fare}</span></div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:rgba(255,255,255,.82);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.07);">
    <span>🛣️ {dist} km × KES 35</span><span>KES {f.distance_charge}</span></div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:rgba(255,255,255,.82);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.07);">
    <span>🏷️ Booking fee</span><span>KES {f.booking_fee}</span></div>
  <div style="display:flex;justify-content:space-between;font-size:15px;font-weight:700;color:#25D366;padding:10px 0 2px;border-top:2px solid rgba(37,211,102,.35);margin-top:8px;">
    <span>💳 Total</span><span style="font-size:22px;">KES {fare}</span></div>
</div>
""", unsafe_allow_html=True)


def render_payment_card(state: dict):
    fare    = state.get("fare_kes", 0)
    pay_url = state.get("pesapal_pay_url", "#")
    status  = state.get("payment_status", "pending")
    is_mock = state.get("pesapal_order_id", "").startswith("MOCK-")

    demo_badge = ""
    if is_mock:
        demo_badge = '<div style="background:rgba(255,169,77,.12);border:1px solid rgba(255,169,77,.3);color:#ffa94d;border-radius:8px;padding:5px 10px;font-size:11.5px;margin-bottom:10px;">🧪 Demo mode — no real charge</div>'

    status_note = ""
    if status == "failed":
        status_note = '<div style="color:#ff6b6b;font-size:13px;margin-top:10px;">❌ Payment failed — please retry</div>'
    elif status == "pending":
        status_note = '<div style="color:#ffa94d;font-size:13px;margin-top:10px;">⏳ Awaiting payment…</div>'

    st.markdown(f"""
<div class="payment-card">
  <div style="color:#6495ed;font-size:15px;font-weight:700;margin-bottom:8px;">💳 Complete Payment</div>
  {demo_badge}
  <div style="font-size:32px;font-weight:800;color:white;margin:6px 0 2px;">KES {fare}</div>
  <div style="font-size:12px;color:rgba(255,255,255,.45);margin-bottom:14px;">Secure via M-Pesa or Card · PesaPal</div>
  <a href="{pay_url}" target="_blank"
     style="display:inline-block;background:#25D366;color:white;font-weight:700;
            padding:11px 28px;border-radius:24px;text-decoration:none;font-size:14px;
            box-shadow:0 3px 12px rgba(37,211,102,.4);">
    💳 Pay KES {fare} via PesaPal →
  </a>
  {status_note}
</div>
""", unsafe_allow_html=True)


def render_confirmed_card(state: dict):
    st.markdown(f"""
<div class="confirmed-card">
  <div style="font-size:18px;font-weight:700;color:white;margin-bottom:14px;">🎉 Booking Confirmed!</div>
  <div style="display:flex;gap:10px;margin:5px 0;font-size:13.5px;color:white;">
    <span style="opacity:.85;min-width:100px;">👤 Passenger</span>
    <span style="font-weight:600;">{state.get('user_name','—')}</span></div>
  <div style="display:flex;gap:10px;margin:5px 0;font-size:13.5px;color:white;">
    <span style="opacity:.85;min-width:100px;">📍 Pickup</span>
    <span style="font-weight:600;">{state.get('pickup_zone','—')}</span></div>
  <div style="display:flex;gap:10px;margin:5px 0;font-size:13.5px;color:white;">
    <span style="opacity:.85;min-width:100px;">🏁 Destination</span>
    <span style="font-weight:600;">{state.get('destination_zone','—')}</span></div>
  <div style="display:flex;gap:10px;margin:5px 0;font-size:13.5px;color:white;">
    <span style="opacity:.85;min-width:100px;">📏 Distance</span>
    <span style="font-weight:600;">{state.get('distance_km','—')} km</span></div>
  <div style="display:flex;gap:10px;margin:5px 0;font-size:13.5px;color:white;">
    <span style="opacity:.85;min-width:100px;">💳 Paid</span>
    <span style="font-weight:600;">KES {state.get('fare_kes','—')} via PesaPal</span></div>
  <div style="display:flex;gap:10px;margin:5px 0;font-size:13.5px;color:white;">
    <span style="opacity:.85;min-width:100px;">⏱ ETA</span>
    <span style="font-weight:600;">5–10 minutes</span></div>
</div>
""", unsafe_allow_html=True)


# ── Session ───────────────────────────────────────────────────────────────────
def init_session():
    if "agent_state" not in st.session_state:
        st.session_state.agent_state = new_state()
        st.session_state.messages    = []
        st.session_state.started     = False

def reset_session():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


# ── Sidebar Info ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗺️ Pilot Zones")
    st.caption("SureRide currently serves these Nairobi neighbourhoods:")
    from utils.zones import ZONE_NAMES
    zones_html = "".join(f'<span class="zone-pill">{z}</span>' for z in sorted(ZONE_NAMES))
    st.markdown(zones_html, unsafe_allow_html=True)
    st.divider()
    st.markdown("### 💰 Pricing")
    st.markdown("""
| Item | Amount |
|------|--------|
| Base fare | KES 150 |
| Per km | KES 35 |
| Booking fee | KES 50 |
| Minimum | KES 300 |
| Surge (×1.5) | Fri/Sat 10PM–3AM |
""")
    st.divider()
    st.markdown("### 📞 Support")
    st.caption("Type **help** in chat anytime")
    st.caption("Email: support@sureride.co.ke")


# ── Main Rendering ────────────────────────────────────────────────────────────
init_session()

tab1, tab2 = st.tabs(["💬 Ride Booking Chat", "📊 Operations Dashboard"])

with tab1:
    # ── Opening greeting ─────────────────────────────────────────────────────
    if not st.session_state.started:
        reply, st.session_state.agent_state = run_turn(st.session_state.agent_state)
        st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
        st.session_state.started = True

    astate = st.session_state.agent_state
    step   = astate.get("current_step", "greet")

    # ── Phone frame (single components.html with everything inside) ───────────
    render_chat(st.session_state.messages)

    # ── Interactive widgets below the phone (centered to phone width) ────────
    st.markdown('<div style="max-width:390px;margin:0 auto;padding:0 8px;">', unsafe_allow_html=True)

    if step == "await_payment":
        render_fare_card(astate)
        render_payment_card(astate)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Check Payment", key="chk"):
                reply, st.session_state.agent_state = run_turn(st.session_state.agent_state, "check")
                st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="canc"):
                reply, st.session_state.agent_state = run_turn(st.session_state.agent_state, "no")
                st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
                st.rerun()

    elif step == "done":
        if astate.get("booking_confirmed"):
            render_confirmed_card(astate)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Book another ride"):
            reset_session()

    elif step == "confirm_fare":
        render_fare_card(astate)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm & Pay", key="cfm"):
                st.session_state.messages.append({"role": "user", "text": "yes", "time": now_time()})
                reply, st.session_state.agent_state = run_turn(st.session_state.agent_state, "yes")
                st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="cncl"):
                st.session_state.messages.append({"role": "user", "text": "no", "time": now_time()})
                reply, st.session_state.agent_state = run_turn(st.session_state.agent_state, "no")
                st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
                st.rerun()

    else:
        user_input = st.chat_input("Type a message…")
        if user_input and user_input.strip():
            st.session_state.messages.append({"role": "user", "text": user_input, "time": now_time()})
            reply, st.session_state.agent_state = run_turn(st.session_state.agent_state, user_input)
            st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    # ── Operations Dashboard view ─────────────────────────────────────────────
    st.markdown('<div class="dash-tab-wrap">', unsafe_allow_html=True)
    st.title("📊 SureRide Operations Dashboard")
    st.caption("iLabAfrica | Strathmore University Capstone Analytics")
    st.markdown("---")
    
    # KPI metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">🚗 Total Bookings</div>
            <div class="metric-value" style="color: #2ea043;">186</div>
            <div style="font-size: 0.85rem; color: #8b949e;">+14% from last week</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">💰 Total Revenue</div>
            <div class="metric-value" style="color: #58a6ff;">KES 111.6K</div>
            <div style="font-size: 0.85rem; color: #8b949e;">Average fare: KES 600</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">⚡ Surge Bookings</div>
            <div class="metric-value" style="color: #d29922;">22.0%</div>
            <div style="font-size: 0.85rem; color: #8b949e;">41 Peak-hour rides</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">💳 Payment Success</div>
            <div class="metric-value" style="color: #bc8cff;">96.8%</div>
            <div style="font-size: 0.85rem; color: #8b949e;">Secured via PesaPal</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphs and charts row
    chart_col, details_col = st.columns([2, 1])
    with chart_col:
        st.markdown("<h4 style='margin-bottom:10px;'>🗺️ Zone Demand Distribution (Bookings)</h4>", unsafe_allow_html=True)
        import pandas as pd
        zone_data = {
            "Zone": ["Westlands", "CBD", "Karen", "Kilimani", "Runda", "Lavington", "South B", "South C", "Gigiri", "Muthaiga"],
            "Bookings": [48, 37, 29, 25, 18, 15, 14, 11, 10, 8]
        }
        df = pd.DataFrame(zone_data).set_index("Zone")
        st.bar_chart(df, color="#2ea043")
        
    with details_col:
        st.markdown("<h4 style='margin-bottom:10px;'>⚖️ Ethics & Safety KPIs</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div class="metric-card" style="margin-bottom: 0.8rem;">
            <div style="font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #f78166;">🚨 Safety Incidents</div>
            <div style="font-size: 20px; font-weight: 700; color: #56d364;">0 Active</div>
            <div style="font-size: 11px; color: #8b949e; margin-top: 2px;">Breathalyzer pass rate: 100%</div>
        </div>
        <div class="metric-card" style="margin-bottom: 0.8rem;">
            <div style="font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #f78166;">🔒 KDPA Compliance</div>
            <div style="font-size: 20px; font-weight: 700; color: #56d364;">Passed</div>
            <div style="font-size: 11px; color: #8b949e; margin-top: 2px;">Data retention: 30 days max</div>
        </div>
        <div class="metric-card">
            <div style="font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #f78166;">⏱️ Operations</div>
            <div style="font-size: 20px; font-weight: 700; color: #58a6ff;">7.4 min</div>
            <div style="font-size: 11px; color: #8b949e; margin-top: 2px;">Average driver dispatch ETA</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recent Transactions Feed
    st.markdown("<h4 style='margin-bottom:10px;'>📋 Recent Transaction Feed (PesaPal Live Audit)</h4>", unsafe_allow_html=True)
    feed_data = [
        {"Reference": "SR-9482", "Passenger": "Brian Omondi", "Route": "Westlands ➔ Karen", "Fare": "KES 960", "PesaPal Ref": "PP-9428104", "Status": "Paid"},
        {"Reference": "SR-9481", "Passenger": "James K.", "Route": "CBD ➔ Kilimani", "Fare": "KES 350", "PesaPal Ref": "PP-9428103", "Status": "Paid"},
        {"Reference": "SR-9480", "Passenger": "Alice W.", "Route": "South B ➔ South C", "Fare": "KES 300", "PesaPal Ref": "PP-9428102", "Status": "Paid"},
        {"Reference": "SR-9479", "Passenger": "David N.", "Route": "Gigiri ➔ Westlands", "Fare": "KES 420", "PesaPal Ref": "PP-9428101", "Status": "Paid"},
        {"Reference": "SR-9478", "Passenger": "Grace M.", "Route": "Runda ➔ Lavington", "Fare": "KES 740", "PesaPal Ref": "PP-9428100", "Status": "Paid"},
    ]
    st.dataframe(pd.DataFrame(feed_data).set_index("Reference"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
