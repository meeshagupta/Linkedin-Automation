import streamlit as st
import time
import os
import json
from bot_core import BotConfig, LinkedInCommentLiker

st.set_page_config(page_title="LinkedIn Bot", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 2rem;}
    .status-box {background: #f0f2f6; padding: 1.5rem; border-radius: 15px; border-left: 6px solid #1f77b4;}
    .mode-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'bot_status' not in st.session_state:
    st.session_state.bot_status = "🟢 Ready"
    st.session_state.logs = []
    st.session_state.running = False
    st.session_state.profile_mode = None
    st.session_state.company_name = None

# Title
st.markdown('<h1 class="main-header">🤖 LinkedIn Dual-Mode Bot</h1>', unsafe_allow_html=True)

# === PROFILE MODE SELECTION ===
col1, col2 = st.columns([1, 3])
with col1:
    st.markdown('<div class="mode-card"><h3>👤 Profile Mode</h3></div>', unsafe_allow_html=True)
    
with col2:
    profile_mode = st.radio(
        "Choose your profile type:",
        ["👤 Personal Profile (New11-GSHEET.py)", "🏢 Company Page (13.py)"],
        index=0,
        horizontal=True,
        help="Personal = New11 logic | Company = 13.py with company switch"
    )

# Dynamic company name input
if profile_mode == "🏢 Company Page (13.py)":
    company_name = st.text_input("🏢 Company Page Name", value="Meeshu automation", 
                               help="Exact company page name from dropdown")
else:
    company_name = ""

# Sidebar: Credentials
st.sidebar.header("🔐 Login Credentials")
email = st.sidebar.text_input("LinkedIn Email", value="shruti.shar10@gmail.com")
password = st.sidebar.text_input("LinkedIn Password", type="password", value="PSabcD@123456!")
sheet_url = st.sidebar.text_input("Google Sheet URL", 
                                value="https://docs.google.com/spreadsheets/d/17bwCB8vbuo96tVHrW6bsBk2sFVd5CSIgYWy1LmofF2k/edit")
creds_file = st.sidebar.file_uploader("📄 Google Service Account JSON", type="json")

# Headless toggle
headless_mode = st.sidebar.checkbox("🖥️ Headless Mode (No browser window)", value=True)

# Main Status Display
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"""
    <div class="status-box">
        <h3>📊 Status: <strong>{st.session_state.bot_status}</strong></h3>
        <p><strong>Mode:</strong> {profile_mode} | <strong>Target:</strong> {company_name or 'Personal'}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 START BOT", use_container_width=True, type="primary") and creds_file:
            st.session_state.profile_mode = profile_mode
            st.session_state.company_name = company_name if company_name else None
            st.session_state.running = True
            st.session_state.bot_status = "🔄 Initializing..."
            st.rerun()
    
    with col_btn2:
        if st.button("🛑 STOP", use_container_width=True):
            st.session_state.running = False
            st.session_state.bot_status = "🛑 Stopped"
            st.session_state.logs = []
            st.rerun()

# Live Logs
st.subheader("📋 Live Logs")
log_container = st.container(height=500)
with log_container:
    if st.session_state.logs:
        for log in st.session_state.logs[-20:]:
            st.text(log)
    else:
        st.info("👈 Click START BOT to begin...")

# === BOT EXECUTION (NON-BLOCKING) ===
if (st.session_state.running and creds_file and st.session_state.profile_mode):
    # SINGLE EXECUTION - NO REPEATED RERUNS
    if "bot_step" not in st.session_state:
        st.session_state.bot_step = "save_creds"

    with log_container:
        try:
            if st.session_state.bot_step == "save_creds":
                credspath = "tempcreds.json"
                with open(credspath, "wb") as f:
                    f.write(creds_file.getvalue())
                st.session_state.logs.append("✅ Credentials saved")
                st.session_state.bot_step = "set_mode"
                st.rerun()

            elif st.session_state.bot_step == "set_mode":
                if "Personal Profile (New11-GSHEET.py)" in st.session_state.profile_mode:
                    st.session_state.bot_mode = "new11"
                else:
                    st.session_state.bot_mode = "13"
                st.session_state.logs.append(f"🎯 Mode: {st.session_state.bot_mode}")
                st.session_state.bot_step = "init_bot"
                st.rerun()

            elif st.session_state.bot_step == "init_bot":
                config = BotConfig(
                    linkedin_email=email,
                    linkedin_password=password,
                    google_sheet_url=sheet_url,
                    company_page_name=st.session_state.company_name,
                    google_credentials_file="tempcreds.json",
                    headless_mode=headless_mode,
                    mode=st.session_state.bot_mode
                )
                st.session_state.config = config
                st.session_state.logs.append("🤖 Initializing bot...")
                st.session_state.bot_step = "create_bot"
                st.rerun()

            elif st.session_state.bot_step == "create_bot":
                st.session_state.bot = LinkedInCommentLiker(st.session_state.config)
                st.session_state.logs.append("🔐 Logging into LinkedIn...")
                st.session_state.bot_step = "login"
                st.rerun()

            elif st.session_state.bot_step == "login":
                st.session_state.bot.initialize()
                st.session_state.logs.append("✅ Login successful!")
                st.session_state.bot_status = "🔄 Processing posts..."
                st.session_state.bot_step = "run_bot"
                st.rerun()

            elif st.session_state.bot_step == "run_bot":
                st.session_state.logs.append("📊 Processing posts...")
                st.session_state.bot.run()
                st.session_state.bot_status = "✅ COMPLETED!"
                st.session_state.logs.append("🎉 Mission complete!")
                st.session_state.running = False
                st.session_state.bot_step = "done"
                st.rerun()

        except Exception as e:
            error_msg = str(e)[:100]
            st.session_state.bot_status = f"❌ ERROR: {error_msg}"
            st.session_state.logs.append(f"❌ Error: {error_msg}")
            st.session_state.running = False
            st.session_state.bot_step = None
            st.rerun()

if st.sidebar.button("💥 EMERGENCY STOP", type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# Instructions
with st.expander("📖 How to Use", expanded=True):
    st.markdown("""
    ### 🎮 **Step-by-Step:**
    1. **Choose Profile Mode** 👆 (Personal = New11 | Company = 13.py)
    2. **Enter Company Name** (if Company mode - exact name from LinkedIn dropdown)
    3. **Fill credentials** (pre-filled for testing)
    4. **Upload** `credentials.json` (Google Service Account with Sheets API enabled)
    5. **Click START BOT** 🚀

    ### 🔍 **What Each Mode Does:**
    | Mode | Script | Profile | Company Switch |
    |------|--------|---------|----------------|
    | 👤 **Personal** | New11-GSHEET.py | ✅ Personal only | ❌ No switch |
    | 🏢 **Company** | 13.py | ✅ Both (tries company first) | ✅ Switches to company |

    ### ✅ **Expected Results in Google Sheet:**
    ```
    Personal: PERSONAL:Glaztower
    Company:  COMPANY:Glaztower  
    POST_ONLY, FAILED also possible
    ```

    ### 📝 **Google Sheet Format:**
    ```
    Post Url | Name | Status
    https://... | Glaztower | [Bot fills this]
    ```

    **💡 Pro Tip:** Bot targets comments from your TARGET_NAMES list in bot_core.py (Glaztower, etc.)
    """)

# Debug info
if creds_file:
    st.sidebar.success("✅ Credentials OK!")
    st.sidebar.caption(f"Mode detected: {profile_mode}")
else:
    st.sidebar.warning("⚠️ Upload credentials.json")

# Clean temp files on stop
if not st.session_state.running and os.path.exists("tempcreds.json"):
    try:
        os.remove("tempcreds.json")
    except:
        pass
