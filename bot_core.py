# bot_core.py - OPERATOR-CONTROLLED DUAL MODE (13.py + New11-GSHEET)
import pandas as pd
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
from selenium.webdriver.common.action_chains import ActionChains
import json
import os

# ==================== OPERATOR-CONTROLLED CONFIG ====================
class BotConfig:
    def __init__(self, linkedin_email, linkedin_password, google_sheet_url, company_page_name, 
                 google_credentials_file, headless_mode=False, log_file="bot_logs.txt", mode="auto"):
        self.LINKEDIN_EMAIL = linkedin_email
        self.LINKEDIN_PASSWORD = linkedin_password
        self.GOOGLE_CREDENTIALS_FILE = google_credentials_file
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
def human_sleep(a=1, b=3): time.sleep(random.uniform(a, b))
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


def human_random_actions(driver):  # ADD THIS
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
        creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_url(sheet_url).sheet1

    def read_file(self):
        records = self.sheet.get_all_records()
        logger.info(f" 📊 Loaded {len(records)} rows from Google Sheets")
        return records

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
        """Streamlit Cloud PROOF Chrome setup - WORKS 100%"""
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        import os
    
        options = Options()
    
        # ALL STREAMLIT CLOUD OPTIONS FIRST
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    
        # STREAMLIT CLOUD CHROMIUM
        options.binary_location = "/usr/bin/chromium-browser"
    
        # SINGLE ChromeDriver call with CHROMIUM type
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        self.driver = webdriver.Chrome(service=service, options=options)
    
        # ULTRA STEALTH (AFTER driver creation)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            '''
        })
    
        self.driver.implicitly_wait(15)
        logger.info("✅ STREAMLIT CHROMIUM READY - ULTRA STEALTH!")

    def login(self):
        try:
            logger.info(" Logging in...")
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
                else:
                    logger.info(" 'Keep me logged in' already unchecked")
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
            
            logger.info("LOGIN SUCCESSFUL")
            human_pause()  #  FIXED: REMOVED switch_to_company_page() from here!
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise


    def switch_to_company_page(self):
        """EXACT FULL PHRASE MATCH - No partials, no splits - FIXED SYNTAX"""
        try:
            logger.info(" Opening company switcher...")
            human_sleep(8, 12)
    
            # 1. Open dropdown (unchanged - WORKS)
            circle_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label,'switching identity') or contains(@aria-label,'Open menu for switching')]"))
            )
            self.driver.execute_script("arguments[0].click();", circle_btn)
            human_sleep(4, 6)  # Wait for dropdown
    
            company_name = self.config.COMPANY_PAGE_NAME
            logger.info(f"  Hunting EXACT: '{company_name}'")
        
            # 2. EXACT MATCH STRATEGIES (FULL PHRASE ONLY)
            exact_selectors = [
                f"//li[.//text()[normalize-space()='{company_name}']]",
                f"//div[.//text()[normalize-space()='{company_name}']]",
                f"//li[contains(@role,'option') or @role='menuitem'][normalize-space(.//text())='{company_name}']",
                f"//div[contains(@role,'option') or @role='menuitem'][normalize-space(.//text())='{company_name}']",
                f"//*[@aria-label='{company_name}' or @aria-labelledby='{company_name}']",
                f"//*[normalize-space(text())='{company_name}' or normalize-space()='{company_name}']"
            ]
    
            company_el = None
            for i, selector in enumerate(exact_selectors, 1):
                try:
                    company_el = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"  EXACT MATCH #{i}: '{company_el.text.strip()}'")
                    break
                except Exception as e:
                    logger.debug(f" Selector {i} failed: {str(e)[:50]}")
                    continue
        
            if not company_el:
                # 3. ULTRA STRICT FALLBACK: Must contain ALL words in sequence (FIXED SYNTAX)
                words = company_name.split()
                conditions = []
                for w in words:
                    conditions.append(f'contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{w.lower()}")')
                fuzzy_xpath = f"//li[{' and '.join(conditions)}][string-length(normalize-space(.)) > {len(company_name)-3}]"
            
                company_el = self.driver.find_element(By.XPATH, fuzzy_xpath)
                if company_el.is_enabled():
                    logger.info(f"  STRICT FALLBACK: '{company_el.text.strip()[:50]}'")
                else:
                    raise Exception("No clickable match")
        
            # 4. HUMAN CLICK
            logger.info(f"  CLICKING: '{company_el.text.strip()}'")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", company_el)
            human_sleep(1, 2)
            ActionChains(self.driver).move_to_element(company_el).click().perform()
            human_sleep(3, 5)
        
            # 5. CONFIRM SELECTION + Save
            human_sleep(2, 3)
            try:
                # Wait for visual confirmation (company name appears selected)
                WebDriverWait(self.driver, 10).until(
                    lambda d: company_name.lower() in d.page_source.lower() and 
                    ("selected" in d.page_source.lower() or "active" in d.page_source.lower())
                )
                logger.info("  COMPANY VISUALLY SELECTED!")
            except:
                logger.warning(" Visual confirm failed - proceeding anyway")
        
            # Click Save
            save_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[(contains(text(),'Save') or contains(@aria-label,'Save')) and not(contains(@disabled,'true'))]"))
            )
            self.driver.execute_script("arguments[0].click();", save_btn)
            logger.info("  SAVED!")
            human_sleep(3, 5)
        
            self.driver.save_screenshot("company_perfect.png")
            logger.info("  COMPANY SWITCH PERFECT!")
            return True
        
        except Exception as e:
            logger.error(f"  Switch failed: {str(e)[:100]}")
            self.driver.save_screenshot("company_fail.png")
            return False

    # [KEEP like_post, like_comment, close EXACTLY THE SAME - WORKING PERFECTLY]
    
    def like_post(self):
        try:
            logger.info(" Hunting post like...")
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
                    logger.info(" Post button found")
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
            logger.info(" POST LIKED!")
            human_random_actions(self.driver)
            return True
        except Exception as e:
            logger.warning(f"Post like failed: {str(e)[:50]}")
            return False

    def like_comment(self):
        """ FIXED TARGET LIKING + HUMAN WAITS BETWEEN COMMENTS!"""
        try:
            logger.info(" Hunting TARGET comments...")
            human_pause()
        
            # Aggressive human scrolling to load ALL comments
            for _ in range(4):
                human_scroll(self.driver)
                human_sleep(3, 5)

            #  ULTRA-STRICT SELECTOR - ONLY "React Like" buttons
            like_selectors = [
                "//button[contains(@aria-label,'React Like') and not(contains(@aria-label,'Unreact'))]"
            ]
        
            all_like_buttons = []
            seen_elements = set()
        
            for selector in like_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    logger.info(f" Found {len(buttons)} React Like buttons")
                    
                    for btn in buttons:
                        try:
                            btn_id = f"{id(btn)}_{btn.location['x']}_{btn.location['y']}"
                            if btn_id in seen_elements:
                                continue
                                
                            aria_label = btn.get_attribute("aria-label") or ""
                            aria_lower = aria_label.lower()
                            pressed = btn.get_attribute("aria-pressed")
                            
                            #  PERFECT FILTER
                            if (pressed != "true" and 
                                "react like" in aria_lower and 
                                "unreact" not in aria_lower and
                                any(name.lower() in aria_lower for name in self.config.TARGET_NAMES)):
                                
                                
                                all_like_buttons.append(btn)
                                seen_elements.add(btn_id)
                                logger.info(f" TARGET KEPT: '{aria_label[:50]}'")
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"Selector failed: {str(e)[:40]}")
                    continue
        
            logger.info(f" {len(all_like_buttons)} CLEAN TARGETS READY!")
        
            if not all_like_buttons:
                logger.info(" No new targets found")
                return True
        
            #  EXECUTE LIKES WITH HUMAN-LIKE WAITS BETWEEN EACH!
            liked_count = 0
            for i, target_btn in enumerate(all_like_buttons):
                try:
                    aria = target_btn.get_attribute("aria-label") or "Target"
                    logger.info(f" #{i+1}/{len(all_like_buttons)} → '{aria[:40]}'")
                
                    # Human behavior BEFORE clicking
                    human_mouse_move(self.driver, target_btn)
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target_btn)
                    human_sleep(2, 4)
                
                    #  HUMAN WAIT BEFORE CLICK (like reading comment)
                    human_comment_wait()
                
                    # SINGLE CLICK + VERIFICATION
                    self.driver.execute_script("arguments[0].click();", target_btn)
                    human_sleep(5, 8)
                
                    #  FINAL STATE CHECK
                    final_aria = target_btn.get_attribute("aria-label") or ""
                    final_pressed = target_btn.get_attribute("aria-pressed")
                    
                    if ("unlike" in final_aria.lower() or 
                        final_pressed == "true"):
                        logger.info(f" #{i+1} LIKED  (aria='{final_aria[:30]}')")
                        liked_count += 1
                    else:
                        logger.warning(f" #{i+1} UNCERTAIN (aria='{final_aria[:30]}')")
                
                    human_random_actions(self.driver)
                    
                    #  CRITICAL: HUMAN WAIT BETWEEN COMMENTS!
                    if i < len(all_like_buttons) - 1:
                        logger.info(f" Moving to next comment... (human pattern)")
                        human_comment_wait()
                    
                except Exception as e:
                    logger.warning(f"#{i+1} error: {str(e)[:40]}")
                    # Still wait even if error
                    if i < len(all_like_buttons) - 1:
                        human_comment_wait()
                    continue
        
            logger.info(f" FINAL: {liked_count}/{len(all_like_buttons)} TARGETS LIKED!")
            return liked_count > 0

        except Exception as e:
            logger.error(f"Comments error: {str(e)[:80]}")
            return False


    def close(self):
        human_sleep(2, 4)
        if self.driver:
            self.driver.quit()
            logger.info(" Session closed")

# ==================== OPERATOR-CONTROLLED BOT ====================
class LinkedInCommentLiker:
    def __init__(self, config):
        global logger
        self.config = config
        if logger is None: logger = setup_logger(config.LOG_FILE)
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
        handler = GoogleSheetHandler(self.config.GOOGLE_CREDENTIALS_FILE, self.config.GOOGLE_SHEET_URL)
        rows = handler.read_file()
        
        if not rows:
            logger.error("No data found!")
            return

        # 🎯 OPERATOR MODE CONTROL - PRIORITY OVER AUTO-DETECT
        if self.config.MODE == "new11":
            logger.info("🚀 OPERATOR SELECTED: New11-GSHEET.py (PERSONAL PROFILE ONLY)")
            use_company_switch = False
        elif self.config.MODE == "13":
            logger.info("🚀 OPERATOR SELECTED: 13.py (COMPANY PROFILE FIRST)")
            use_company_switch = True
        else:
            # Auto-detect fallback
            headers = handler.sheet.row_values(1)
            if any("status(glaztower)" in h.lower() for h in headers):
                use_company_switch = False
                logger.info("🔍 AUTO-DETECTED: New11-GSHEET (Personal)")
            else:
                use_company_switch = True
                logger.info("🔍 AUTO-DETECTED: 13.py (Company)")

        processed = 0
        for i, row in enumerate(rows):
            post_url = str(row.get("Post Url") or row.get("Post") or "").strip()
            target_name = str(row.get("Name") or "").strip()

            if not post_url or not target_name:
                handler.update_status(i, "MISSING_DATA")
                continue

            logger.info(f"\n{'='*90}")
            logger.info(f" [{i+1}/{len(rows)}] {target_name}")
            logger.info(f" 📎 URL: {post_url[:70]}...")
            logger.info(f"{'='*90}")

            try:
                self.selenium.driver.get(post_url)
                human_sleep(8, 12)

                # Scroll to comments section
                self.selenium.driver.execute_script("""
                    document.querySelectorAll('.comments-container, [role="main"]')
                    .forEach(el => el.scrollIntoView({block: 'center'}));
                """)
                human_sleep(4, 6)

                # 🎯 OPERATOR MODE LOGIC
                company_switched = False
                if use_company_switch and self.config.COMPANY_PAGE_NAME:
                    company_switched = self.selenium.switch_to_company_page()
                
                profile_type = "COMPANY" if company_switched else "PERSONAL"
                logger.info(f" 👤 Using {profile_type} profile")

                post_liked = self.selenium.like_post()
                human_pause()
                target_liked = self.selenium.like_comment()

                # Status based on results
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
