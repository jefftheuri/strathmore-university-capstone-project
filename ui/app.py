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
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 SureRide")
    st.caption("Nairobi Night Rides · Pilot Mode")
    view = st.radio(
        "**Navigate**",
        ["💬 Ride Booking Chat", "📊 Operations Dashboard"],
        index=0
    )
    st.divider()

# ── Global page CSS ───────────────────────────────────────────────────────────
if view == "💬 Ride Booking Chat":
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }
body, .stApp, [data-testid="stAppViewContainer"], .main,
[data-testid="stMain"], [data-testid="stMainBlockContainer"],
.block-container { background: #efeae2 !important; }
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
.block-container {
    padding: 0 !important;
    max-width: 540px !important;
}
/* Chat input at bottom */
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
/* Buttons */
.stButton > button {
    border-radius: 24px !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    font-size: 14px !important;
    transition: all .15s !important;
    border: none !important;
}
/* Action button row */
div[data-testid="column"]:first-child .stButton > button {
    background: #25d366 !important; color: white !important;
    box-shadow: 0 2px 8px rgba(37,211,102,.4) !important;
}
div[data-testid="column"]:last-child .stButton > button {
    background: #ffffff !important; color: #333 !important;
    border: 1px solid #d9dbdb !important;
}
/* Sidebar */
section[data-testid="stSidebar"] { background: #f0f4f0 !important; }
.zone-pill {
    display: inline-block;
    background: rgba(37,211,102,.12);
    border: 1px solid rgba(37,211,102,.3);
    color: #0a7a41; border-radius: 12px;
    padding: 3px 10px; font-size: 11.5px;
    font-weight: 500; margin: 2px;
}
/* Fare / payment / confirmed cards */
.fare-card, .payment-card, .confirmed-card {
    border-radius: 14px; padding: 16px 18px;
    margin: 6px 0 10px; font-family: 'Inter', sans-serif;
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
</style>
""", unsafe_allow_html=True)
else:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }
body, .stApp, [data-testid="stAppViewContainer"], .main,
[data-testid="stMain"], [data-testid="stMainBlockContainer"],
.block-container {
    background: #0d1117 !important;
    color: #c9d1d9 !important;
}
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
.block-container {
    max-width: 1100px !important;
    padding: 2rem 1.5rem !important;
}
/* Sidebar */
section[data-testid="stSidebar"] { background: #161b22 !important; border-right: 1px solid #30363d !important; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
.zone-pill {
    display: inline-block;
    background: rgba(56,139,253,0.15);
    border: 1px solid rgba(56,139,253,0.4);
    color: #58a6ff; border-radius: 12px;
    padding: 3px 10px; font-size: 11.5px;
    font-weight: 500; margin: 2px;
}
/* Sleek card styling */
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

def _build_chat_html(messages: list) -> str:
    date_str = datetime.now().strftime("%A, %d %B %Y")
    bubbles = ""
    for msg in messages:
        html_text = md_to_html(msg["text"])
        ts        = msg["time"]
        if msg["role"] == "bot":
            bubbles += f"""
<div class="msg-row msg-row-bot">
  <div class="bubble bubble-bot">
    <span class="msg-text">{html_text}</span>
    <div class="msg-meta">
      <span class="msg-time">{ts}</span>
    </div>
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
<head><meta charset="UTF-8">
<style>{_CHAT_CSS}</style>
</head>
<body>
<div class="chat-wrap">
  <div class="day-chip"><span>{date_str}</span></div>
  {bubbles}
</div>
<script>window.scrollTo(0,document.body.scrollHeight);</script>
</body>
</html>"""


def render_chat(messages: list):
    if not messages:
        return
    # Estimate height: ~90px per message, min 200, max 700
    h = min(max(len(messages) * 88, 160), 700)
    components.html(_build_chat_html(messages), height=h, scrolling=True)


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

if view == "💬 Ride Booking Chat":
    # ── WhatsApp header ──────────────────────────────────────────────────────
    components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
* { margin:0; padding:0; box-sizing:border-box;
    font-family: -apple-system,'Segoe UI','Inter',sans-serif; }
body { background: #008069; }
.header {
    display: flex; align-items: center; gap: 14px;
    padding: 10px 14px; background: #008069;
}
.back { color: white; font-size: 22px; cursor: pointer; margin-right: -4px; }
.avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: #25D366; display: flex;
    align-items: center; justify-content: center; font-size: 20px;
    flex-shrink: 0;
}
.info { flex: 1; }
.name   { font-size: 16px; font-weight: 600; color: white; }
.status { font-size: 12px; color: #b2dfdb; margin-top: 1px; }
.icons  { display: flex; gap: 18px; color: white; font-size: 20px; }
</style>
</head>
<body>
<div class="header">
  <div class="back">←</div>
  <div class="avatar">🚗</div>
  <div class="info">
    <div class="name">SureRide</div>
    <div class="status">🟢 online</div>
  </div>
  <div class="icons">
    <span title="Video call">📹</span>
    <span title="Call">📞</span>
    <span title="More">⋮</span>
  </div>
</div>
</body>
</html>
""", height=62)

    # ── Opening greeting ──────────────────────────────────────────────────────
    if not st.session_state.started:
        reply, st.session_state.agent_state = run_turn(st.session_state.agent_state)
        st.session_state.messages.append({"role": "bot", "text": reply, "time": now_time()})
        st.session_state.started = True

    # ── Render all chat messages ──────────────────────────────────────────────
    render_chat(st.session_state.messages)

    astate = st.session_state.agent_state
    step   = astate.get("current_step", "greet")

    # ── Step-specific UI ──────────────────────────────────────────────────────
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

else:
    # ── Operations Dashboard view ─────────────────────────────────────────────
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

