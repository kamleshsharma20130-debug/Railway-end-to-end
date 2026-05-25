import os
import sys
import time
import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

# =========================================================
#               RAILWAY REAL-TIME LOGGING FIX
# =========================================================
os.environ["PYTHONUNBUFFERED"] = "1"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

logger = logging.getLogger("railway")

def log(msg=""):
    logger.info(msg)
def clear_screen():
    pass
def success(msg):
    log(f"[SUCCESS] {msg}")
def error(msg):
    log(f"[ERROR] {msg}")
def info(msg):
    log(f"[INFO] {msg}")
def get_current_time():
    ist = ZoneInfo("Asia/Kolkata")
    return datetime.now(ist).strftime(
        "%d-%m-%Y %I:%M:%S %p IST"
    )
    
# =========================================================
#                   MAIN CLASS
# =========================================================
class FacebookMessenger:

    def __init__(self):
        self.driver = None
        self.wait = None
        self.cookies_list = []
        self.current_cookie_index = 0
        self.message_index = 0
        self.target_uid = ""
        self.messages = []
        self.haters_name = ""
        self.delay = 10

        # MEMORY CLEANUP INTERVAL
        self.cleanup_interval = 10

    # =====================================================
    #               SAFE WAI. FUNCTION
    # =====================================================
    def safe_wait(self, condition, timeout=60):

        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=0.5
            ).until(condition)

        except TimeoutException:
            return False

    # =====================================================
    #               DRIVER HEALTH CHECK
    # =====================================================
    def driver_alive(self):

        try:

            self.driver.execute_script(
                "return 1"
            )

            return True

        except Exception as e:

            error(f"DRIVER DEAD : {e}")

            return False

    # =====================================================
    #               SOFT RESET TAB
    # =====================================================
    def soft_refresh_chat(self):

        try:

            info("SOFT RESETTING TAB")

            # DESTROY OLD HEAVY TAB
            self.driver.get("about:blank")

            time.sleep(3)

            # REOPEN SAME SESSION CHAT
            self.driver.get(
                f"https://www.facebook.com/messages/e2ee/t/{self.target_uid}"
            )

            # WAIT FULL LOAD
            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                120
            )

            if not loaded:
                raise Exception("CHAT PAGE LOAD FAILED")

            # WAIT MESSAGE BOX
            ready = self.safe_wait(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@contenteditable='true']"
                    )
                ),
                120
            )

            if not ready:
                raise Exception("CHAT BOX LOAD FAILED")

            success("TAB SOFT RESET COMPLETE")

            return True

        except Exception as e:

            error(f"SOFT RESET FAILED : {e}")

            return False

    # =====================================================
    #                   AUTO LOAD
    # =====================================================
    def auto_load(self):

        try:

            self.cookies_list = [
                line.strip()
                for line in open(
                    "cookies.txt",
                    "r",
                    encoding="utf-8"
                )
                if line.strip()
            ]

            self.target_uid = open(
                "target_uid.txt",
                "r",
                encoding="utf-8"
            ).read().strip()

            self.messages = [
                x.strip()
                for x in open(
                    "messages.txt",
                    "r",
                    encoding="utf-8"
                )
                if x.strip()
            ]

            if os.path.exists("hatersname.txt"):

                self.haters_name = open(
                    "hatersname.txt",
                    "r",
                    encoding="utf-8"
                ).read().strip()

            if os.path.exists("time.txt"):

                self.delay = int(
                    open("time.txt").read().strip()
                )

            if (
                not self.cookies_list
                or not self.target_uid
                or not self.messages
            ):
                raise Exception("FILES EMPTY OR MISSING")

            success("ALL FILES AUTO-LOADED SUCCESSFULLY")

            log(
                f"[CONFIG] "
                f"[TOTAL_COOKIES: {len(self.cookies_list)}] "
                f"[TARGET: {self.target_uid}] "
                f"[TOTAL_MSGS: {len(self.messages)}] "
                f"[DELAY: {self.delay}s]"
            )

            return True

        except Exception as e:

            error(f"AUTO LOAD FAILED : {e}")

            return False

    # =====================================================
    #                   DRIVER SETUP
    # =====================================================
    def setup_driver(self):

        try:

            options = Options()

            # =================================================
            #           HEADLESS + STABLE MODE
            # =================================================
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            options.page_load_strategy = "normal"

            # =================================================
            #               MEMORY OPTIMIZATION
            # =================================================
            options.add_argument("--max_old_space_size=128")

            options.add_argument(
                "--disable-renderer-backgrounding"
            )

            options.add_argument(
                "--disable-background-timer-throttling"
            )

            options.add_argument(
                "--disable-backgrounding-occluded-windows"
            )

            options.add_argument("--disable-gpu")
            
            options.add_argument(
                   "--disable-features=NetworkService"
            )

            options.add_argument(
                "--disable-features=site-per-process"
            )

            options.add_argument(
                "--disable-features=IsolateOrigins"
            )

            options.add_argument(
                "--disable-features=CalculateNativeWinOcclusion"
            )

            options.add_argument("--disable-breakpad")

            options.add_argument(
                "--disable-component-update"
            )

            # =================================================
            #               IMAGE DISABLE
            # =================================================
            options.add_argument(
                "--blink-settings=imagesEnabled=false"
            )

            # =================================================
            #               EXTRA PERFORMANCE
            # =================================================
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-infobars")

            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-default-apps")

            options.add_argument("--window-size=1280,720")

            # =================================================
            #               LOW STORAGE MODE
            # =================================================
            options.add_argument(
                "--disk-cache-size=1"
            )

            options.add_argument(
                "--media-cache-size=1"
            )

            options.add_argument(
                "--disable-application-cache"
            )

            # =================================================
            #               CHROME LOG REDUCTION
            # =================================================
            options.add_argument("--log-level=3")

            options.add_experimental_option(
                "excludeSwitches",
                ["enable-logging"]
            )

            service = Service(
                "/usr/bin/chromedriver"
            )

            self.driver = webdriver.Chrome(
                service=service,
                options=options
            )

            self.wait = WebDriverWait(
                self.driver,
                40
            )

            success("CHROME DRIVER STARTED")
            success("LOW MEMORY MODE ENABLED")
            success("RAILWAY LOGGING FIX ENABLED")

            return True

        except Exception as e:

            error(f"DRIVER ERROR : {e}")

            return False

    # =====================================================
    #           LOGIN USING COOKIES (STABLE)
    # =====================================================
    def login_with_cookies(self):

        return self.switch_cookie(0)

    def switch_cookie(self, cookie_no):

        try:

            cookie_str = self.cookies_list[cookie_no]

            info(f"SWITCHING TO COOKIE #{cookie_no + 1}")

            # FACEBOOK OPEN
            self.driver.get("https://www.facebook.com")

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                60
            )

            if not loaded:
                raise Exception("FACEBOOK LOAD FAILED")

            # CLEAR OLD COOKIES
            self.driver.delete_all_cookies()

            time.sleep(2)

            cookies = cookie_str.split(";")

            added = 0

            for cookie in cookies:

                if "=" in cookie:

                    name, value = cookie.strip().split(
                        "=",
                        1
                    )

                    try:

                        self.driver.add_cookie({
                            "name": name,
                            "value": value,
                            "domain": ".facebook.com"
                        })

                        added += 1

                    except:
                        pass

            success(
                f"COOKIE #{cookie_no + 1} LOADED : {added}"
            )

            # SESSION REFRESH
            self.driver.get(
                f"https://www.facebook.com/messages/e2ee/t/{self.target_uid}"
            )

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                120
            )

            if not loaded:
                raise Exception("CHAT LOAD FAILED")

            ready = self.get_message_box()

            if not ready:
                raise Exception("CHAT BOX FAILED")

            success(
                f"COOKIE #{cookie_no + 1} ACTIVE"
            )

            return True

        except Exception as e:

            error(
                f"COOKIE SWITCH FAILED : {e}"
            )

            return False

    # =====================================================
    #                   GET MESSAGE BOX
    # =====================================================
    def get_message_box(self):

        return self.safe_wait(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@contenteditable='true']"
                )
            ),
            120
        )

    # =====================================================
    #                   SEND MESSAGE
    # =====================================================
    def send_message(self, text):

        try:

            if not self.driver_alive():
                return False

            # =================================================
            #               PAGE READY
            # =================================================
            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                120
            )

            if not loaded:
                raise Exception("PAGE LOAD TIMEOUT")

            # =================================================
            #               GET FRESH BOX
            # =================================================
            box = self.get_message_box()

            if not box:
                raise Exception("MESSAGE BOX NOT FOUND")

            # =================================================
            #               SCROLL + FOCUS
            # =================================================
            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center'
                });
                """,
                box
            )

            self.driver.execute_script(
                "arguments[0].focus();",
                box
            )

            focused = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.activeElement === arguments[0]",
                    box
                ),
                30
            )

            if not focused:
                raise Exception("BOX FOCUS FAILED")

            # =================================================
            #               FINAL MESSAGE
            # =================================================
            final_msg = (
                f"{self.haters_name} {text}"
            ).strip()

            # =================================================
            #               CLEAR OLD TEXT
            # =================================================
            box.send_keys(
                Keys.CONTROL,
                "a"
            )

            box.send_keys(Keys.BACKSPACE)

            time.sleep(1)

            # =================================================
            #               RE-GET BOX
            # =================================================
            box = self.driver.find_element(
                By.XPATH,
                "//div[@contenteditable='true']"
            )

            # =================================================
            #               TYPE MESSAGE
            # =================================================
            box.send_keys(final_msg)

            typed = self.safe_wait(
                lambda d: final_msg in box.text,
                60
            )

            if not typed:
                raise Exception("MESSAGE TYPE FAILED")

            # =================================================
            #               RANDOM STABILITY DELAY
            # =================================================
            time.sleep(
                random.uniform(1.5, 3.5)
            )

            # =================================================
            #               SEND MESSAGE
            # =================================================
            box.send_keys(Keys.ENTER)

            # =================================================
            #               SEND CONFIRM
            # =================================================
            sent = self.safe_wait(
                lambda d: box.text.strip() == "",
                60
            )

            if not sent:
                raise Exception("MESSAGE SEND FAILED")

            # =================================================
            #               EXTRA STABILITY
            # =================================================
            stable = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                30
            )

            if not stable:
                raise Exception("POST SEND STABILITY FAILED")

            time.sleep(
                random.uniform(1.5, 2.5)
            )

            return True

        except (
            TimeoutException,
            StaleElementReferenceException,
            WebDriverException,
            Exception
        ) as e:

            error(f"SEND FAILED : {e}")

            try:

                self.soft_refresh_chat()

            except:
                pass

            return False

    # =====================================================
    #                       START
    # =====================================================
    def start(self):

        clear_screen()

        info("LOADING CONFIGURATION")

        if not self.auto_load():
            return

        if not self.setup_driver():
            return

        if not self.login_with_cookies():
            return

        info("OPENING E2EE CHAT")

        self.driver.get(
            f"https://www.facebook.com/messages/e2ee/t/{self.target_uid}"
        )

        loaded = self.safe_wait(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete",
            60
        )

        if not loaded:

            error("CHAT PAGE LOAD FAILED")

            return

        chat_ready = self.safe_wait(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@contenteditable='true']"
                )
            ),
            60
        )

        if not chat_ready:

            error("CHAT FAILED TO OPEN")

            return

        success("MESSAGE SENDING STARTED")

        count = 0

        while True:

            current_cookie = (
                self.current_cookie_index
                % len(self.cookies_list)
            )

            # COOKIE SWITCH
            switched = self.switch_cookie(
                current_cookie
            )

            if not switched:

                error(
                    f"COOKIE #{current_cookie + 1} FAILED"
                )

                self.current_cookie_index += 1

                continue

            # CURRENT MESSAGE
            msg = self.messages[
                self.message_index
                % len(self.messages)
            ]

            current_time = get_current_time()

            sent = self.send_message(msg)

            count += 1

            short_msg = (
                msg[:60] + "..."
                if len(msg) > 60
                else msg
            )

            status = (
                "SUCCESS"
                if sent
                else "FAILED"
            )

            # LOG
            log(
                f"[MSG #{count}] "
                f"[COOKIE #{current_cookie + 1}] "
                f"[TARGET: {self.target_uid}] "
                f"[TIME: {current_time}] "
                f"[STATUS: {status}] "
                f"[MESSAGE: {short_msg}]"
            )

            log(
                f"[ALIVE] "
                f"[COOKIE #{current_cookie + 1}] "
                f"BOT RUNNING | "
                f"MSG #{count}"
            )

            log(
                "───────────────────────────────────────────────────────────────"
            )

            # NEXT MESSAGE
            self.message_index += 1

            # NEXT COOKIE
            self.current_cookie_index += 1

            # MEMORY CLEANUP
            if count % self.cleanup_interval == 0:

                self.soft_refresh_chat()

            # SAFE DELAY
            for _ in range(self.delay):

                time.sleep(1)

                if not self.driver_alive():

                    error("DRIVER CRASH DETECTED")

                    return

# =========================================================
#                       RUN SCRIPT
# =========================================================
if __name__ == "__main__":
    bot = FacebookMessenger()
    bot.start()