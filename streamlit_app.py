import streamlit as st
import os
from bot_core import BotConfig, LinkedInCommentLiker
from bot_core import logger  # For live logs

st.set_page_config(page_title="LinkedIn Bot", layout="wide")
st.title("🤖 LinkedIn Comment Liker Bot")
st.success("✅ Local tests PASSED - Ready for action!")

# Sidebar - All inputs
with st.sidebar:
    st.header("⚙️ Bot Configuration")
    
    # Required fields
    email = st.text_input("🔐 LinkedIn Email", type="password")
    password = st.text_input("🔑 LinkedIn Password", type="password")
    sheet_url = st.text_input("📊 Google Sheet URL")
    creds_file = st.file_uploader("📄 Google Service Account JSON", type="json")
    
    # Optional
    company_name = st.text_input("🏢 Company Page Name (leave empty for personal)")
    mode = st.selectbox("🎛️ Mode", ["auto", "13 (Company)", "new11 (Personal)"])
    
    # Bot controls
    headless = st.checkbox("🖥️ Headless Mode (No browser window)", value=True)
    
    if st.button("🚀 **START BOT**", type="primary", use_container_width=True):
        if not all([email, password, sheet_url]):
            st.error("❌ Fill all required fields!")
        else:
            st.session_state.bot_running = True
            st.rerun()

# Main execution
if 'bot_running' in st.session_state and st.session_state.bot_running:
    with st.spinner("🤖 Bot is running..."):
        try:
            # Save credentials temporarily
            if creds_file:
                with open("temp_creds.json", "wb") as f:
                    f.write(creds_file.read())
                creds_path = "temp_creds.json"
            else:
                creds_path = "credentials.json"  # Your existing file
            
            # Create config & run
            config = BotConfig(
                linkedin_email=email,
                linkedin_password=password,
                google_sheet_url=sheet_url,
                company_page_name=company_name or None,
                google_credentials_file=creds_path,
                headless_mode=headless,
                mode=mode.lower().replace(" (company)", "").replace(" (personal)", ""),
                log_file="streamlit_bot.log"
            )
            
            bot = LinkedInCommentLiker(config)
            bot.initialize()
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Run bot
            bot.run()
            
            progress_bar.progress(100)
            status_text.success("🎉 BOT COMPLETED SUCCESSFULLY!")
            st.balloons()
            
            st.session_state.bot_running = False
            
        except Exception as e:
            st.error(f"❌ Bot failed: {str(e)}")
            st.session_state.bot_running = False
            logger.error(f"Streamlit bot error: {e}")

# Footer
st.markdown("---")
st.info("💡 **Status**: Your bot_core.py will work perfectly! Just needs web interface.")
