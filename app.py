import streamlit as st
import os
from bot_core import BotConfig, LinkedInCommentLiker, LinkedInVerificationRequired, clear_cookies

st.set_page_config(page_title="LinkedIn Bot", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 2rem;}
    .status-box {background: #f0f2f6; padding: 1.5rem; border-radius: 15px; border-left: 6px solid #1f77b4;}
    .mode-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE INIT ====================
if 'bot_status' not in st.session_state:
    st.session_state.bot_status = "🟢 Ready"
    st.session_state.logs = []
    st.session_state.running = False
    st.session_state.profile_mode = None
    st.session_state.company_name = None

# ==================== TITLE ====================
st.markdown('<h1 class="main-header">🤖 LinkedIn Dual-Mode Bot</h1>', unsafe_allow_html=True)

# ==================== PROFILE MODE SELECTION ====================
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
    company_name = st.text_input("🏢 Company Page Name", value="",
                                 help="Exact company page name from LinkedIn dropdown")
else:
    company_name = ""

# ==================== SIDEBAR CREDENTIALS ====================
# Each user fills in their own credentials — designed for multi-user deployment.
st.sidebar.header("🔐 Login Credentials")
email = st.sidebar.text_input(
    "LinkedIn Email",
    placeholder="you@example.com"
)
password = st.sidebar.text_input(
    "LinkedIn Password",
    type="password",
    placeholder="Your LinkedIn password"
)
sheet_url = st.sidebar.text_input(
    "Google Sheet URL",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)
creds_file = st.sidebar.file_uploader("📄 Google Service Account JSON", type="json")

# Headless must be True on Streamlit Cloud (no display available)
headless_mode = st.sidebar.checkbox("🖥️ Headless Mode (No browser window)", value=True)

# ==================== STATUS DISPLAY ====================
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
        start_clicked = st.button("🚀 START BOT", use_container_width=True, type="primary")
        if start_clicked:
            if not creds_file:
                # ✅ FIX 2: Show visible warning instead of silently ignoring missing creds
                st.warning("⚠️ Please upload credentials.json first!")
            elif not email or not password or not sheet_url:
                st.warning("⚠️ Please fill in all credentials!")
            else:
                st.session_state.profile_mode = profile_mode
                st.session_state.company_name = company_name if company_name else None
                st.session_state.running = True
                st.session_state.bot_status = "🔄 Initializing..."
                # ✅ FIX 3: Explicitly set bot_step on every fresh start.
                # Previously bot_step was only set if missing, so after an error
                # (which set it to None) a new START would skip all steps silently.
                st.session_state.bot_step = "save_creds"
                st.rerun()

    with col_btn2:
        if st.button("🛑 STOP", use_container_width=True):
            st.session_state.running = False
            st.session_state.bot_status = "🛑 Stopped"
            st.session_state.logs = []
            # ✅ FIX 3 (cont): Clear bot_step on stop so next START begins fresh
            st.session_state.pop("bot_step", None)
            st.rerun()

# ==================== LIVE LOGS ====================
st.subheader("📋 Live Logs")
log_container = st.container(height=500)
with log_container:
    if st.session_state.logs:
        for log in st.session_state.logs[-20:]:
            st.text(log)
    else:
        st.info("👈 Click START BOT to begin...")

# ==================== BOT EXECUTION ====================
if st.session_state.running and creds_file and st.session_state.profile_mode:

    # Safety guard: should always be set by the START button now
    if "bot_step" not in st.session_state or st.session_state.bot_step is None:
        st.session_state.bot_step = "save_creds"

    with log_container:
        try:
            if st.session_state.bot_step == "save_creds":
                # ✅ FIX 4: Use /tmp/ — guaranteed writable on Streamlit Cloud.
                # The repo root may be read-only in cloud deployments.
                credspath = "/tmp/tempcreds.json"
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
                    google_credentials_file="/tmp/tempcreds.json",  # ✅ FIX 4 (cont)
                    headless_mode=headless_mode,
                    mode=st.session_state.bot_mode
                )
                st.session_state.config = config
                st.session_state.logs.append("🤖 Bot config ready...")
                st.session_state.bot_step = "create_bot"
                st.rerun()

            elif st.session_state.bot_step == "create_bot":
                st.session_state.bot = LinkedInCommentLiker(st.session_state.config)
                st.session_state.logs.append("🔐 Logging into LinkedIn...")
                st.session_state.bot_step = "login"
                st.rerun()

            elif st.session_state.bot_step == "login":
                try:
                    st.session_state.bot.initialize()
                    st.session_state.logs.append("✅ Login successful! (session saved)")
                    st.session_state.bot_status = "🔄 Processing posts..."
                    st.session_state.bot_step = "run_bot"
                    st.rerun()
                except LinkedInVerificationRequired:
                    st.session_state.logs.append("📧 LinkedIn sent a verification code to your email!")
                    st.session_state.logs.append("👇 Enter the code below to continue...")
                    st.session_state.bot_status = "⏳ Waiting for verification code..."
                    st.session_state.bot_step = "verify_input"
                    st.rerun()

            elif st.session_state.bot_step == "verify_input":
                pass  # UI below handles this step

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
            # ✅ FIX 5: Pop bot_step entirely after error (not set to None).
            # Setting to None kept the key in session_state, causing the safety guard
            # above to NOT trigger on next START, so steps were silently skipped.
            st.session_state.pop("bot_step", None)
            st.rerun()

# ==================== VERIFICATION CODE INPUT ====================
if st.session_state.get("bot_step") == "verify_input":
    st.markdown("---")
    st.warning("### 📧 LinkedIn Verification Required!")
    st.markdown(
        "LinkedIn sent a **6-digit code** to your email address **" +
        (email[:4] + "****" + email[email.find("@"):] if email and "@" in email else "your email") +
        "**. Check your inbox (and spam folder) and enter it below."
    )
    col_v1, col_v2 = st.columns([2, 1])
    with col_v1:
        verify_code = st.text_input(
            "🔑 Verification Code",
            placeholder="e.g. 123456",
            max_chars=8,
            key="verify_code_input"
        )
    with col_v2:
        st.write("")
        st.write("")
        if st.button("✅ Submit Code", type="primary", use_container_width=True):
            if verify_code.strip():
                with st.spinner("Verifying..."):
                    try:
                        st.session_state.bot.selenium.submit_verification_code(verify_code.strip())
                        st.session_state.logs.append("✅ Verified! Session saved — no more codes needed!")
                        st.session_state.bot_status = "🔄 Processing posts..."
                        st.session_state.bot_step = "run_bot"
                        st.rerun()
                    except Exception as e:
                        st.session_state.logs.append(f"❌ Wrong code or expired: {str(e)[:60]}")
                        st.session_state.bot_status = "❌ Verification failed — try again"
                        st.session_state.running = False
                        st.session_state.pop("bot_step", None)
                        st.rerun()
            else:
                st.warning("⚠️ Please enter the code first!")
    st.markdown("---")

# ==================== EMERGENCY STOP ====================
if st.sidebar.button("💥 EMERGENCY STOP", type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    try:
        os.remove("/tmp/tempcreds.json")
    except Exception:
        pass
    st.rerun()

# ==================== INSTRUCTIONS ====================
with st.expander("📖 How to Use", expanded=False):
    st.markdown("""
    ### 🎮 **Step-by-Step:**
    1. **Choose Profile Mode** 👆 (Personal = New11 | Company = 13.py)
    2. **Enter Company Name** (if Company mode — exact name from LinkedIn dropdown)
    3. **Fill credentials** in sidebar (or pre-load via Streamlit Secrets)
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
    """)

# ==================== SIDEBAR STATUS ====================
# Clear saved session button — forces fresh login next time
if email:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🍪 Saved Session**")
    import hashlib, os as _os
    _cookie_path = f"/tmp/li_session_{hashlib.md5(email.encode()).hexdigest()[:12]}.json"
    if _os.path.exists(_cookie_path):
        st.sidebar.success("✅ Session saved — no verification needed!")
        if st.sidebar.button("🗑️ Clear Saved Session", help="Force fresh login next time"):
            clear_cookies(email)
            st.sidebar.warning("Session cleared — next login will require verification")
            st.rerun()
    else:
        st.sidebar.info("ℹ️ No saved session yet")
        st.sidebar.caption("After first login + verification, session is saved automatically")


if creds_file:
    st.sidebar.success("✅ Credentials file OK!")
    st.sidebar.caption(f"Mode: {profile_mode}")
else:
    st.sidebar.warning("⚠️ Upload credentials.json")

# ==================== TEMP FILE CLEANUP ====================
if not st.session_state.running and os.path.exists("/tmp/tempcreds.json"):
    try:
        os.remove("/tmp/tempcreds.json")
    except Exception:
        pass
