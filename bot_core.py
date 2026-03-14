# bot_core.py - PRODUCTION READY FOR STREAMLIT CLOUD + GITHUB (ALL FIXES)
import time
import random
import logging
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import os

# ==================== OPERATOR-CONTROLLED CONFIG ====================
class BotConfig:
    def __init__(self, linkedin_email, linkedin_password, google_sheet_url, company_page_name, 
                 google_credentials_file, headless_mode=False, log_file="/tmp/bot_logs.txt", mode="auto"):
        self.LINKEDIN_EMAIL = linkedin_email
        self.LINKEDIN_PASSWORD = linkedin_password
        self.GOOGLE_CREDENTIALS_FILE = google_credentials_file  # ✅ FIXED
        self.GOOGLE_SHEET_URL = google_sheet_url
        self.COMPANY_PAGE_NAME = company_page_name
        self.MODE = mode  # "13" (Company), "new11" (Personal), or "auto"
        self.MIN_DELAY = 25
        self.MAX_DELAY = 50
        self.COMMENT_MIN_WAIT = 12
        self.COMMENT_MAX_WAIT = 25
        self.HEADLESS_MODE = headless_mode
        self.LOG_FILE = log_file
        self.TARGET_NAMES = [
            "Bim Sphere", "Anuj Kumar Gupta", "Glaztower", "Ayush Nagar Koti",
            "BrikAtrium", "Coolrise", "Structoria", "Design Veil", "PLENORISE",
            "AXIALITH", "SILLTRACE", "Nitin Gupta", "Vimal Yadav", "Sagar Rawat",
        ]

# ==================== LOGGER ====================
def setup_logger(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("LinkedInBot")

logger = None

# ==================== STEALTH HELPERS ====================
def human_sleep(a=1, b=3): 
    time.sleep(random.uniform(a, b))

def human_pause(): 
    pause = random.uniform(4, 15)
    logger.info(f" 🤔 Human thinking... {pause:.1f}s")
    time.sleep(pause)

def human_scroll(driver):
    for _ in range(random.randint(2, 5)):
        driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)});")
        human_sleep(0.5, 1.5)

def human_mouse_move(driver, element):
    ActionChains(driver).move_to_element(element).perform()
    human_sleep(0.3, 0.8)

def human_type(element, text):
    for ch in text: 
        element.send_keys(ch)
        time.sleep(random.uniform(0.08, 0.25))
    human_sleep(1, 3)

def human_comment_wait():
    wait_time = random.uniform(12, 25)
    logger.info(f" 📖 Reading comment... {wait_time:.1f}s")
    time.sleep(wait_time)

def human_random_actions(driver):
    """Random human-like micro-actions after liking"""
    action = random.choice([
        lambda: human_sleep(0.3, 0.8),
        lambda: driver.execute_script("window.scrollBy(0, %d);" % random.randint(-100, 100)),
        lambda: human_pause()
    ])
    action()

# ==================== GOOGLE SHEET HANDLER ====================
class GoogleSheetHandler:
    def __init__(self, credentials_file, sheet_url):
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        try:
            creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_url(sheet_url).sheet1
            logger.info("✅ Google Sheets connected successfully")
        except Exception as e:
            logger.error(f"❌ Google Sheets connection failed: {str(e)}")
            self.sheet = None

    def readfile(self):
        if not self.sheet:
            logger.error("No sheet available - check credentials/sheet URL")
            return []
        try:
            records = self.sheet.get_all_records()
            logger.info(f"📊 Loaded {len(records)} rows from Google Sheets")
            return records
        except Exception as e:
            logger.error(f"Read failed: {str(e)}")
            return []

    def update_status(self, row_index, status):
        try:
            headers = self.sheet.row_values(1)
            status_col = None
            for col_num, header in enumerate(headers, 1):
                if "status" in header.lower():
                    status_col = col_num
                    logger.info(f" 📍 Status column #{status_col}: '{header}'")
                    break
            
            if status_col:
                row_num = row_index + 2
                self.sheet.update_cell(row_num, status_col, f"{status} @ {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f" ✅ Updated Row {row_num}: {status}")
        except Exception as e:
            logger.error(f" ❌ Status update failed: {e}")


# ==================== RUNTIME CHROME INSTALLER ====================
def ensure_chrome_installed():
    """
    Install Chrome at runtime using sudo + urllib (no wget, no root needed directly).
    packages.txt is ignored on Streamlit Cloud — this is the only reliable fix.
    """
    import subprocess
    import urllib.request

    check_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    if any(os.path.exists(p) for p in check_paths):
        logger.info("✅ Chrome already installed — skipping")
        return

    logger.info("🌐 Chrome not found — starting runtime install...")

    def run_cmd(cmd, timeout=300):
        """Run shell command, return (success, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if out:
                logger.info(f"  {out[:300]}")
            if err and result.returncode != 0:
                logger.warning(f"  {err[:300]}")
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"  cmd error: {str(e)[:100]}")
            return False

    # ── METHOD 1: sudo apt-get chromium-browser (Ubuntu) ──
    logger.info("📦 Method 1: sudo apt-get chromium-browser...")
    run_cmd("sudo apt-get update -qq", timeout=120)
    ok = run_cmd("sudo apt-get install -y -qq chromium-browser chromium-chromedriver", timeout=300)
    if ok and any(os.path.exists(p) for p in check_paths):
        logger.info("✅ Chromium installed via apt-get!")
        return

    # ── METHOD 2: sudo apt-get chromium (Debian name) ──
    logger.info("📦 Method 2: sudo apt-get chromium...")
    ok = run_cmd("sudo apt-get install -y -qq chromium chromium-driver", timeout=300)
    if ok and any(os.path.exists(p) for p in check_paths):
        logger.info("✅ Chromium (Debian) installed!")
        return

    # ── METHOD 3: Download Google Chrome .deb via Python urllib (no wget needed) ──
    logger.info("📦 Method 3: Downloading Google Chrome .deb via Python urllib...")
    chrome_url = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    deb_path = "/tmp/google-chrome.deb"
    try:
        logger.info(f"  Downloading from {chrome_url}...")
        urllib.request.urlretrieve(chrome_url, deb_path)
        logger.info(f"  Download complete — installing .deb...")
        run_cmd(f"sudo apt-get install -y -qq {deb_path}", timeout=300)
        run_cmd("sudo apt-get install -y -qq -f", timeout=120)  # fix broken deps
        if any(os.path.exists(p) for p in check_paths):
            logger.info("✅ Google Chrome installed via .deb!")
            return
    except Exception as e:
        logger.warning(f"  .deb download/install failed: {str(e)[:150]}")

    # ── METHOD 4: pip install playwright as absolute last resort ──
    logger.info("📦 Method 4: Trying playwright chromium...")
    try:
        run_cmd("pip install playwright -q", timeout=120)
        run_cmd("python -m playwright install chromium", timeout=300)
        run_cmd("python -m playwright install-deps chromium", timeout=300)
        pw_paths = [
            os.path.expanduser("~/.cache/ms-playwright"),
            "/root/.cache/ms-playwright",
            "/home/adminuser/.cache/ms-playwright",
        ]
        for pw_path in pw_paths:
            if os.path.exists(pw_path):
                logger.info(f"✅ Playwright chromium found at {pw_path}")
                return
    except Exception as e:
        logger.warning(f"  Playwright failed: {str(e)[:100]}")

    logger.error(
        "❌ ALL install methods failed.\n"
        "The Streamlit Cloud container does not allow installing Chrome.\n"
        "Consider deploying on a VPS (Railway, Render, EC2) instead."
    )

# ==================== SELENIUM CLIENT ====================
class LinkedInSeleniumClient:
    def __init__(self, email, password, headless=False, config=None):
        self.email = email
        self.password = password
        self.headless = headless
        self.config = config
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """🔥 BULLETPROOF - Works EVERYWHERE (Streamlit Cloud + Local)"""
        ensure_chrome_installed()
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # ✅ FIX: Set chromium binary location explicitly for Streamlit Cloud
        chromium_binaries = [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/lib/chromium/chromium",
        ]
        for binary in chromium_binaries:
            if os.path.exists(binary):
                options.binary_location = binary
                logger.info(f"✅ Chromium binary found: {binary}")
                break

        # ✅ FIX: Build driver path list LAZILY — never call .install() eagerly in a list.
        # Eagerly calling ChromeDriverManager().install() causes 'NoneType has no attribute split'
        # when chromium is not in PATH, because the result (None) gets passed to Service().
        def get_driver_paths():
            static_paths = [
                "/usr/bin/chromedriver",                  # Streamlit Cloud (chromium-driver pkg)
                "/usr/lib/chromium/chromedriver",          # Debian alternative
                "/usr/lib/chromium-browser/chromedriver",  # Ubuntu alternative
                "/snap/bin/chromium.chromedriver",         # Snap install
            ]
            for p in static_paths:
                if os.path.exists(p):
                    yield p

            # Only try webdriver-manager as last resort, and guard against None return
            try:
                path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                if path:
                    yield path
            except Exception:
                pass
            try:
                path = ChromeDriverManager().install()
                if path:
                    yield path
            except Exception:
                pass

        self.driver = None
        for attempt, path in enumerate(get_driver_paths(), 1):
            try:
                logger.info(f"🔄 [attempt {attempt}] Trying: {str(path)[:60]}...")
                service = Service(executable_path=path)
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info(f"✅ [attempt {attempt}] DRIVER READY with: {path}")
                break
            except Exception as e:
                logger.warning(f"❌ [attempt {attempt}] Failed: {str(e)[:80]}")
                continue

        if not self.driver:
            raise Exception(
                "❌ NO WORKING CHROMEDRIVER FOUND.\n"
                "Ensure your packages.txt (not package.txt!) contains:\n"
                "  chromium\n  chromium-driver\n  xvfb"
            )
        
        # Stealth (only if driver exists)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        })
        self.driver.implicitly_wait(15)
        logger.info("🚀 STEALTH MODE ACTIVATED!")

    def login(self):
        try:
            logger.info("🔐 Logging in...")
            self.driver.get("https://www.linkedin.com/login")
            human_sleep(4, 7)
            human_scroll(self.driver)

            email_el = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            human_mouse_move(self.driver, email_el)
            human_type(email_el, self.email)
            human_pause()

            password_el = self.driver.find_element(By.ID, "password")
            human_mouse_move(self.driver, password_el)
            human_type(password_el, self.password)
            human_pause()

            # UNCHECK "Keep me logged in"
            try:
                remember_checkbox = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox' and (@name='remember' or contains(@aria-label,'Remember') or contains(@id,'remember'))]"))
                )
                if remember_checkbox.is_selected():
                    logger.info(" Unchecking 'Keep me logged in'...")
                    self.driver.execute_script("arguments[0].click();", remember_checkbox)
                    human_sleep(1, 2)
            except:
                logger.info(" No 'Keep me logged in' checkbox found")

            login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            human_mouse_move(self.driver, login_btn)
            human_sleep(2, 4)
            login_btn.click()
            
            human_pause()
            WebDriverWait(self.driver, 60).until(
                EC.any_of(EC.url_contains("feed"), EC.url_contains("checkpoint"))
            )
            logger.info("✅ LOGIN SUCCESSFUL")
            human_pause()
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            raise

    def switch_to_company_page(self):
        """✅ FIXED: NULL CHECK + No split() crash"""
        try:
            # ✅ FIX 1: NULL CHECK FOR PERSONAL MODE
            if not self.config.COMPANY_PAGE_NAME:
                logger.warning("🏢 No company name provided - skipping switch (Personal mode)")
                return False
                
            company_name = self.config.COMPANY_PAGE_NAME
            logger.info(f"🏢 Opening company switcher for: '{company_name}'")
            human_sleep(8, 12)

            circle_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label,'switching identity') or contains(@aria-label,'Open menu for switching')]"))
            )
            self.driver.execute_script("arguments[0].click();", circle_btn)
            human_sleep(4, 6)

            exact_selectors = [
                f"//li[.//text()[normalize-space()='{company_name}']]",
                f"//div[.//text()[normalize-space()='{company_name}']]",
                f"//li[contains(@role,'option') or @role='menuitem'][normalize-space(.//text())='{company_name}']",
            ]
    
            company_el = None
            for i, selector in enumerate(exact_selectors, 1):
                try:
                    company_el = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f" ✅ EXACT MATCH #{i}: '{company_el.text.strip()}'")
                    break
                except:
                    continue
        
            if not company_el:
                raise Exception(f"No company match: {company_name}")
        
            logger.info(f" 👆 CLICKING: '{company_el.text.strip()}'")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", company_el)
            human_sleep(1, 2)
            ActionChains(self.driver).move_to_element(company_el).click().perform()
            human_sleep(3, 5)

            save_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[(contains(text(),'Save') or contains(@aria-label,'Save')) and not(contains(@disabled,'true'))]"))
            )
            self.driver.execute_script("arguments[0].click();", save_btn)
            logger.info(" ✅ COMPANY SWITCHED!")
            human_sleep(3, 5)
            return True
        
        except Exception as e:
            logger.error(f" ❌ Company switch failed: {str(e)[:100]}")
            return False

    def like_post(self):
        try:
            logger.info(" 👍 Hunting post like...")
            human_pause()
            human_scroll(self.driver)
            
            selectors = [
                "//button[contains(@aria-label,'Like')]",
                "//button[contains(@aria-label,'React Like')]",
                "//button[@data-control-name*='like']"
            ]
        
            post_btn = None
            for selector in selectors:
                try:
                    post_btn = WebDriverWait(self.driver, 12).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue
        
            if not post_btn:
                logger.warning(" No post like button")
                return False
            
            if post_btn.get_attribute("aria-pressed") == "true":
                logger.info(" Post already liked")
                return True
            
            human_mouse_move(self.driver, post_btn)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", post_btn)
            human_pause()
            self.driver.execute_script("arguments[0].click();", post_btn)
            human_sleep(3, 5)
            logger.info(" ✅ POST LIKED!")
            human_random_actions(self.driver)
            return True
        except Exception as e:
            logger.warning(f"Post like failed: {str(e)[:50]}")
            return False

    def like_comment(self):
        """TARGET LIKING + HUMAN WAITS"""
        try:
            logger.info(" 🎯 Hunting TARGET comments...")
            human_pause()
        
            for _ in range(4):
                human_scroll(self.driver)
                human_sleep(3, 5)

            like_selectors = ["//button[contains(@aria-label,'React Like') and not(contains(@aria-label,'Unreact'))]"]
            all_like_buttons = []
            seen_elements = set()
        
            for selector in like_selectors:
                buttons = self.driver.find_elements(By.XPATH, selector)
                logger.info(f" Found {len(buttons)} React Like buttons")
                
                for btn in buttons:
                    try:
                        btn_id = f"{id(btn)}_{btn.location['x']}_{btn.location['y']}"
                        if btn_id in seen_elements:
                            continue
                        
                        aria_label = btn.get_attribute("aria-label") or ""
                        if ("react like" in aria_label.lower() and 
                            "unreact" not in aria_label.lower() and
                            any(name.lower() in aria_label.lower() for name in self.config.TARGET_NAMES)):
                            
                            all_like_buttons.append(btn)
                            seen_elements.add(btn_id)
                            logger.info(f" ✅ TARGET: '{aria_label[:50]}'")
                    except:
                        continue
        
            if not all_like_buttons:
                logger.info(" No targets found")
                return True
        
            liked_count = 0
            for i, target_btn in enumerate(all_like_buttons):
                try:
                    aria = target_btn.get_attribute("aria-label") or "Target"
                    logger.info(f" #{i+1}/{len(all_like_buttons)} → '{aria[:40]}'")
                
                    human_mouse_move(self.driver, target_btn)
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target_btn)
                    human_sleep(2, 4)
                    human_comment_wait()
                
                    self.driver.execute_script("arguments[0].click();", target_btn)
                    human_sleep(5, 8)
                    
                    final_aria = target_btn.get_attribute("aria-label") or ""
                    if "unlike" in final_aria.lower():
                        logger.info(f" #{i+1} ✅ LIKED!")
                        liked_count += 1
                    
                    human_random_actions(self.driver)
                    if i < len(all_like_buttons) - 1:
                        human_comment_wait()
                    
                except Exception as e:
                    logger.warning(f"#{i+1} error: {str(e)[:40]}")
                    continue
        
            logger.info(f" 🎉 {liked_count}/{len(all_like_buttons)} TARGETS LIKED!")
            return liked_count > 0

        except Exception as e:
            logger.error(f"Comments error: {str(e)[:80]}")
            return False

    def close(self):
        human_sleep(2, 4)
        if self.driver:
            self.driver.quit()
            logger.info(" ✅ Session closed")

# ==================== MAIN BOT ====================
class LinkedInCommentLiker:
    def __init__(self, config):
        global logger
        self.config = config
        if logger is None: 
            logger = setup_logger(config.LOG_FILE)
        self.selenium = None

    def initialize(self):
        self.selenium = LinkedInSeleniumClient(
            self.config.LINKEDIN_EMAIL,
            self.config.LINKEDIN_PASSWORD,
            self.config.HEADLESS_MODE,
            self.config
        )
        self.selenium.login()

    def run(self):
        # ✅ FIXED ATTRIBUTE ERRORS
        handler = GoogleSheetHandler(
            self.config.GOOGLE_CREDENTIALS_FILE,  # ✅ FIXED
            self.config.GOOGLE_SHEET_URL          # ✅ FIXED
        )
        rows = handler.readfile()
        if not rows:
            logger.error("❌ No data found or sheet access failed!")
            return
    
        # Operator mode control
        if self.config.MODE == "new11":
            logger.info("🎯 Mode: new11 (👤 Personal Profile)")
            use_company_switch = False
        elif self.config.MODE == "13":
            logger.info("🎯 Mode: 13 (🏢 Company Page)")
            use_company_switch = True
        else:
            try:
                headers = handler.sheet.row_values(1) if handler.sheet else []
                if any("glaztower" in str(h).lower() for h in headers):
                    use_company_switch = False
                    logger.info("🔍 AUTO-DETECTED: Personal mode")
                else:
                    use_company_switch = True
                    logger.info("🔍 AUTO-DETECTED: Company mode")
            except:
                use_company_switch = False
        
        processed = 0
        for i, row in enumerate(rows):
            post_url = str(row.get("Post Url") or row.get("Post") or "").strip()
            target_name = str(row.get("Name") or "").strip()

            if not post_url or not target_name:
                handler.update_status(i, "MISSING_DATA")
                continue

            logger.info(f"\n{'='*90}")
            logger.info(f" [{i+1}/{len(rows)}] 🎯 {target_name}")
            logger.info(f" 📎 URL: {post_url[:70]}...")
            logger.info(f"{'='*90}")

            try:
                self.selenium.driver.get(post_url)
                human_sleep(8, 12)

                self.selenium.driver.execute_script("""
                    document.querySelectorAll('.comments-container, [role="main"]')
                    .forEach(el => el.scrollIntoView({block: 'center'}));
                """)
                human_sleep(4, 6)

                company_switched = False
                if use_company_switch and self.config.COMPANY_PAGE_NAME:
                    company_switched = self.selenium.switch_to_company_page()
                
                profile_type = "COMPANY" if company_switched else "PERSONAL"
                logger.info(f" 👤 Using {profile_type} profile")

                post_liked = self.selenium.like_post()
                human_pause()
                target_liked = self.selenium.like_comment()

                if target_liked and post_liked:
                    status = f"{profile_type}:{target_name}"
                elif post_liked:
                    status = f"{profile_type}:POST_ONLY"
                else:
                    status = f"{profile_type}:FAILED"

                handler.update_status(i, status)
                logger.info(f" ✅ RESULT: {status}")
                processed += 1

            except Exception as e:
                logger.error(f" ❌ Row {i} failed: {str(e)[:60]}")
                handler.update_status(i, f"ERROR:{str(e)[:20]}")

            if processed < len(rows):
                delay = random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY)
                logger.info(f" ⏳ Stealth wait: {delay:.1f}s")
                time.sleep(delay)

        logger.info(f"\n🎉 MISSION COMPLETE! {processed}/{len(rows)} ({self.config.MODE})")
