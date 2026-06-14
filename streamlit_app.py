"""
streamlit_app.py
AI Medication Reminder — a calm, daily check-in companion.

Run locally:   streamlit run streamlit_app.py
Deploy:        push to GitHub, deploy on share.streamlit.io (Streamlit Community Cloud)
"""

import streamlit as st
import datetime
import os
from dotenv import load_dotenv

from memory import (
    init_db, save_user, get_user, get_all_users,
    mark_dose_taken, increment_missed_doses,
    get_today_status, get_history
)
from agent import analyze_behavior
from notifier import send_email, build_family_alert

# ---------------------------------------------------------------------------
# Page config & global styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Mindful Dose",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="expanded",
)

load_dotenv()

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #1A1F1C;
    --surface: #232925;
    --ink: #EDEAE2;
    --ink-soft: #9CA7A0;
    --sage: #7FB89A;
    --sage-soft: #243029;
    --amber: #E0A867;
    --amber-soft: #332A1E;
    --terracotta: #E08D7D;
    --terracotta-soft: #352321;
    --line: #343B36;
}

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--ink);
}

/* Hide the default menu/footer but KEEP header visible so the sidebar
   toggle arrow remains accessible */
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: transparent;
}

/* Force our text colors to win over Streamlit's theme defaults */
.stApp, .stApp p, .stApp span, .stApp div, .stApp label {
    color: var(--ink);
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.hero-title, .status-card h3 {
    color: var(--ink) !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] * {
    color: var(--ink);
}

/* ---------- Hero ---------- */
.hero {
    padding: 2.2rem 0 0.4rem 0;
    text-align: left;
}
.hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--sage);
    margin-bottom: 0.4rem;
}
.hero-title {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 2.6rem;
    line-height: 1.1;
    margin: 0;
    color: var(--ink);
}
.hero-sub {
    font-size: 1rem;
    color: var(--ink-soft);
    margin-top: 0.5rem;
    max-width: 38ch;
}

/* ---------- Status card ---------- */
.status-card {
    background: var(--surface);
    border-radius: 20px;
    padding: 1.8rem 1.8rem;
    margin: 1.4rem 0;
    border: 1px solid var(--line);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.02) inset;
}
.status-card h3 {
    font-family: 'Fraunces', serif;
    font-weight: 500;
    margin: 0 0 0.2rem 0;
    font-size: 1.3rem;
}
.status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 0.6rem;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.95rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.01em;
}
.pill-taken { background: var(--sage-soft); color: var(--sage); }
.pill-pending { background: var(--amber-soft); color: var(--amber); }
.pill-missed { background: var(--terracotta-soft); color: var(--terracotta); }

.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-taken { background: var(--sage); }
.dot-pending { background: var(--amber); }
.dot-missed { background: var(--terracotta); }

/* ---------- Streak strip (signature element) ---------- */
.streak-wrap {
    margin-top: 1.6rem;
}
.streak-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 0.6rem;
}
.streak-row {
    display: flex;
    gap: 6px;
}
.streak-cell {
    flex: 1;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
}
.cell-taken { background: var(--sage); color: #15211A; }
.cell-missed { background: var(--terracotta-soft); color: var(--terracotta); border: 1px dashed var(--terracotta); }
.cell-none { background: var(--bg); color: var(--ink-soft); border: 1px solid var(--line); }
.cell-today { box-shadow: 0 0 0 2px var(--ink) inset; }

/* ---------- Message card from agent ---------- */
.agent-card {
    border-radius: 20px;
    padding: 1.5rem 1.7rem;
    margin: 1rem 0;
    border-left: 4px solid var(--sage);
    background: var(--sage-soft);
}
.agent-card.urgent { border-left-color: var(--amber); background: var(--amber-soft); }
.agent-card.critical { border-left-color: var(--terracotta); background: var(--terracotta-soft); }

.agent-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 0.4rem;
}
.agent-message {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    line-height: 1.5;
    margin: 0;
}

/* ---------- Buttons ---------- */
div.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    border: 1px solid var(--line);
    padding: 0.6rem 1.2rem;
    transition: all 0.15s ease;
}
div.stButton > button:hover {
    border-color: var(--sage);
    color: var(--sage);
}
div.stButton > button[kind="primary"] {
    background: var(--sage);
    border: none;
    color: #15211A;
}
div.stButton > button[kind="primary"]:hover {
    background: #6BA384;
    color: #15211A;
}

/* ---------- Misc ---------- */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin: 2rem 0 0.6rem 0;
}
.divider {
    height: 1px;
    background: var(--line);
    margin: 1.6rem 0;
    border: none;
}
.activity-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--ink-soft);
    padding: 0.35rem 0;
    border-bottom: 1px dashed var(--line);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
init_db()

def get_secret(key):
    """Reads a config value from environment first, then Streamlit secrets if available."""
    val = os.getenv(key)
    if val:
        return val
    try:
        return st.secrets[key]
    except Exception:
        return None


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
SENDER_EMAIL = get_secret("SENDER_EMAIL")
SENDER_PASSWORD = get_secret("SENDER_PASSWORD")

if "activity_log" not in st.session_state:
    st.session_state.activity_log = []

if "current_user" not in st.session_state:
    st.session_state.current_user = None


def log_activity(text):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.activity_log.insert(0, f"{timestamp} — {text}")
    st.session_state.activity_log = st.session_state.activity_log[:8]


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Daily check-in</div>
    <h1 class="hero-title">Mindful Dose</h1>
    <p class="hero-sub">A quiet daily companion that notices when you've taken
    your medication — and gently escalates if you haven't.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — user switcher / settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Profile")
    existing_users = get_all_users()

    mode = st.radio("Account", ["Existing user", "New user"], label_visibility="collapsed")

    if mode == "Existing user" and existing_users:
        chosen = st.selectbox("Select your name", existing_users)
        if st.button("Switch", use_container_width=True):
            st.session_state.current_user = chosen
            st.rerun()
    else:
        with st.form("new_user_form"):
            new_name = st.text_input("Your name")
            new_med = st.text_input("Medication name")
            new_time = st.text_input("Usual dose time", placeholder="e.g. 08:00 AM")
            family_email = st.text_input("Family member's email (optional)")
            submitted = st.form_submit_button("Create profile", use_container_width=True, type="primary")
            if submitted and new_name and new_med:
                save_user(new_name, new_med, new_time or "08:00 AM")
                st.session_state.current_user = new_name
                st.session_state[f"family_email_{new_name}"] = family_email
                st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    if not GEMINI_API_KEY:
        st.caption("⚠️ No Gemini API key found. Using rule-based reminders. Add GEMINI_API_KEY to .env or Streamlit secrets to enable AI messages.")
    else:
        st.caption("✅ AI-powered messages enabled (Gemini).")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
user_name = st.session_state.current_user

if not user_name:
    st.markdown("""
    <div class="status-card">
        <h3>Get started</h3>
        <p style="color: var(--ink-soft); margin-top: 0.6rem;">
        Create a profile in the sidebar to begin your daily check-ins.
        Mindful Dose will track your streak and gently let your family know
        if you've missed a few doses in a row.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

user_data = get_user(user_name)
today_status = get_today_status(user_name)
history = get_history(user_name, days=14)

# ---------------------------------------------------------------------------
# Status card
# ---------------------------------------------------------------------------
status_map = {
    "taken": ("Taken today", "pill-taken", "dot-taken"),
    "missed": ("Missed today", "pill-missed", "dot-missed"),
    None: ("Awaiting check-in", "pill-pending", "dot-pending"),
}
status_label, pill_class, dot_class = status_map[today_status]

st.markdown(f"""
<div class="status-card">
    <h3>Hi {user_name} 👋</h3>
    <p style="color: var(--ink-soft); margin: 0;">
        {user_data['medication_name']} · scheduled for {user_data['dose_time']}
    </p>
    <div class="status-row">
        <span class="status-pill {pill_class}"><span class="dot {dot_class}"></span>{status_label}</span>
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--ink-soft);">
            {user_data['missed_doses']} missed in a row
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Check-in buttons (only if not yet logged today)
# ---------------------------------------------------------------------------
if today_status is None:
    col1, col2 = st.columns(2)
    with col1:
        took_it = st.button("✅ I took it", use_container_width=True, type="primary")
    with col2:
        missed_it = st.button("⏳ Not yet / missed", use_container_width=True)
else:
    st.caption(f"You've already checked in for today ({status_map[today_status][0].lower()}). Come back tomorrow!")
    took_it = False
    missed_it = False

agent_result = None

if took_it:
    mark_dose_taken(user_name)
    log_activity(f"{user_name} marked today's dose as taken")
    st.toast("Nice work — logged for today! 🌿", icon="✅")
    st.rerun()

if missed_it:
    increment_missed_doses(user_name)
    log_activity(f"{user_name} marked today's dose as missed")
    updated = get_user(user_name)
    agent_result = analyze_behavior(updated, api_key=GEMINI_API_KEY)
    st.session_state["last_agent_result"] = agent_result
    st.session_state["last_agent_user"] = user_name

# Show agent result if we just generated one (persists across the rerun below via session_state)
if "last_agent_result" in st.session_state and st.session_state.get("last_agent_user") == user_name and today_status == "missed":
    agent_result = st.session_state["last_agent_result"]

if agent_result:
    action = agent_result["action"]
    message = agent_result["message"]
    source = agent_result["source"]

    card_class = "agent-card"
    eyebrow = "Gentle reminder"
    if action == "URGENT_ALERT":
        card_class += " urgent"
        eyebrow = "Please take a moment"
    elif action == "NOTIFY_FAMILY":
        card_class += " critical"
        eyebrow = "Letting your family know"

    source_label = "AI-generated" if source == "ai" else "Rule-based"

    st.markdown(f"""
    <div class="{card_class}">
        <div class="agent-eyebrow">{eyebrow} · {source_label}</div>
        <p class="agent-message">{message}</p>
    </div>
    """, unsafe_allow_html=True)

    if action == "NOTIFY_FAMILY":
        family_email = st.session_state.get(f"family_email_{user_name}", "")
        subject, body = build_family_alert(user_name, message)
        success, info = send_email(SENDER_EMAIL, SENDER_PASSWORD, family_email, subject, body)
        log_activity(f"Family notification: {info}")
        if success:
            st.success(f"Family member notified at {family_email}")
        else:
            st.info(f"Simulated: {info}")

# ---------------------------------------------------------------------------
# Streak strip — signature element
# ---------------------------------------------------------------------------
st.markdown('<div class="streak-wrap">', unsafe_allow_html=True)
st.markdown('<div class="streak-label">Last 14 days</div>', unsafe_allow_html=True)

cells_html = '<div class="streak-row">'
today_str = datetime.date.today().isoformat()
for date_str, status in history:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    day_label = str(d.day)
    cell_class = {"taken": "cell-taken", "missed": "cell-missed", "none": "cell-none"}[status]
    if date_str == today_str:
        cell_class += " cell-today"
    cells_html += f'<div class="streak-cell {cell_class}">{day_label}</div>'
cells_html += '</div>'

st.markdown(cells_html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------
if st.session_state.activity_log:
    st.markdown('<div class="section-label">Activity</div>', unsafe_allow_html=True)
    for entry in st.session_state.activity_log:
        st.markdown(f'<div class="activity-line">{entry}</div>', unsafe_allow_html=True)