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
    WebDriverException,
    NoSuchElementException
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

        self.cookie_str = ""
        self.target_uid = ""
        self.messages = []

        self.haters_name = ""
        self.delay = 10

        self.cleanup_interval = 15

    # =====================================================
    #                   SAFE WAIT
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
    #               GET MESSAGE BOX
    # =====================================================

    def get_message_box(self):

        xpaths = [

            "//div[@contenteditable='true']",

            "//div[@role='textbox']",

            "//p[@class]"
        ]

        for xpath in xpaths:

            try:

                box = WebDriverWait(
                    self.driver,
                    20
                ).until(
                    EC.presence_of_element_located(
                        (By.XPATH, xpath)
                    )
                )

                if box:
                    return box

            except:
                pass

        return False

    # =====================================================
    #               SOFT RESET CHAT
    # =====================================================

    def soft_refresh_chat(self):

        try:

            info("SOFT RESETTING CHAT")

            self.driver.get("about:blank")

            time.sleep(3)

            self.driver.get(
                f"https://www.facebook.com/messages/t/{self.target_uid}"
            )

            time.sleep(6)

            ready = self.get_message_box()

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

            self.cookie_str = open(
                "cookies.txt",
                "r",
                encoding="utf-8"
            ).read().strip()

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
                    open(
                        "time.txt"
                    ).read().strip()
                )

            if (
                not self.cookie_str
                or not self.target_uid
                or not self.messages
            ):
                raise Exception("FILES EMPTY")

            success("ALL FILES LOADED")

            return True

        except Exception as e:

            error(f"AUTO LOAD FAILED : {e}")

            return False

    # =====================================================
    #                   SETUP DRIVER
    # =====================================================

    def setup_driver(self):

        try:

            options = Options()

            # =================================================
            #               STABLE HEADLESS
            # =================================================

            options.add_argument("--headless=old")

            options.add_argument("--no-sandbox")

            options.add_argument(
                "--disable-dev-shm-usage"
            )

            options.page_load_strategy = "eager"

            # =================================================
            #               ANTI DETECTION
            # =================================================

            options.add_argument(
                "--disable-blink-features=AutomationControlled"
            )

            options.add_experimental_option(
                "excludeSwitches",
                [
                    "enable-automation",
                    "enable-logging"
                ]
            )

            options.add_experimental_option(
                "useAutomationExtension",
                False
            )

            # =================================================
            #               MEMORY OPTIMIZATION
            # =================================================

            options.add_argument("--disable-gpu")

            options.add_argument(
                "--disable-extensions"
            )

            options.add_argument(
                "--disable-notifications"
            )

            options.add_argument(
                "--disable-popup-blocking"
            )

            options.add_argument(
                "--disable-background-timer-throttling"
            )

            options.add_argument(
                "--disable-renderer-backgrounding"
            )

            options.add_argument(
                "--disable-backgrounding-occluded-windows"
            )

            options.add_argument(
                "--blink-settings=imagesEnabled=false"
            )

            options.add_argument("--window-size=1280,720")

            options.add_argument("--log-level=3")

            service = Service(
                "/usr/bin/chromedriver"
            )

            self.driver = webdriver.Chrome(
                service=service,
                options=options
            )

            # =================================================
            #           REMOVE SELENIUM DETECTION
            # =================================================

            self.driver.execute_script("""
            Object.defineProperty(
                navigator,
                'webdriver',
                {
                    get: () => undefined
                }
            )
            """)

            self.wait = WebDriverWait(
                self.driver,
                40
            )

            success("CHROME DRIVER STARTED")
            success("LOW MEMORY MODE ENABLED")
            success("ANTI DETECTION ENABLED")

            return True

        except Exception as e:

            error(f"DRIVER ERROR : {e}")

            return False

    # =====================================================
    #               LOGIN WITH COOKIES
    # =====================================================

    def login_with_cookies(self):

        try:

            info("OPENING FACEBOOK")

            self.driver.get(
                "https://www.facebook.com"
            )

            time.sleep(5)

            cookies = self.cookie_str.split(";")

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

            success(f"COOKIES LOADED : {added}")

            self.driver.get(
                "https://www.facebook.com/messages"
            )

            time.sleep(8)

            success("LOGIN SUCCESSFUL")

            return True

        except Exception as e:

            error(f"COOKIE LOGIN FAILED : {e}")

            return False

    # =====================================================
    #                   SEND MESSAGE
    # =====================================================

    def send_message(self, text):

        try:

            if not self.driver_alive():
                return False

            final_msg = (
                f"{self.haters_name} {text}"
            ).strip()

            # ============================================
            #       OPEN CHAT EVERY SEND
            # ============================================

            self.driver.get(
                f"https://www.facebook.com/messages/t/{self.target_uid}"
            )

            time.sleep(
                random.uniform(5, 8)
            )

            # ============================================
            #       GET FRESH MESSAGE BOX
            # ============================================

            box = self.get_message_box()

            if not box:
                raise Exception("MESSAGE BOX NOT FOUND")

            # ============================================
            #       CLICK + FOCUS
            # ============================================

            self.driver.execute_script(
                "arguments[0].click();",
                box
            )

            time.sleep(2)

            # ============================================
            #       CLEAR OLD MESSAGE
            # ============================================

            try:

                box.send_keys(
                    Keys.CONTROL,
                    "a"
                )

                box.send_keys(
                    Keys.BACKSPACE
                )

            except:
                pass

            time.sleep(1)

            # ============================================
            #       RE-GET FRESH BOX
            # ============================================

            box = self.get_message_box()

            if not box:
                raise Exception("FRESH BOX FAILED")

            # ============================================
            #       SLOW TYPING
            # ============================================

            for char in final_msg:

                box.send_keys(char)

                time.sleep(
                    random.uniform(0.02, 0.06)
                )

            time.sleep(
                random.uniform(2, 4)
            )

            # ============================================
            #       SEND MESSAGE
            # ============================================

            box.send_keys(Keys.ENTER)

            time.sleep(
                random.uniform(4, 7)
            )

            success("MESSAGE SENT")

            return True

        except (
            TimeoutException,
            StaleElementReferenceException,
            WebDriverException,
            NoSuchElementException,
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

        info("OPENING CHAT")

        self.driver.get(
            f"https://www.facebook.com/messages/t/{self.target_uid}"
        )

        time.sleep(8)

        success("MESSAGE SENDING STARTED")

        count = 0

        while True:

            for msg in self.messages:

                if not self.driver_alive():

                    error("DRIVER CRASH DETECTED")

                    return

                current_time = get_current_time()

                sent = self.send_message(msg)

                count += 1

                if count % self.cleanup_interval == 0:

                    self.soft_refresh_chat()

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

                log(
                    f"[MSG #{count}] "
                    f"[TARGET: {self.target_uid}] "
                    f"[TIME: {current_time}] "
                    f"[STATUS: {status}] "
                    f"[MESSAGE: {short_msg}]"
                )

                log(
                    f"[ALIVE] BOT RUNNING | "
                    f"MSG #{count} | "
                    f"{current_time}"
                )

                log(
                    "────────────────────────────────────────────"
                )

                for _ in range(self.delay):

                    time.sleep(1)

                    if not self.driver_alive():

                        error("DRIVER CRASH DETECTED")

                        return

# =========================================================
#                       RUN
# =========================================================

if __name__ == "__main__":

    bot = FacebookMessenger()

    bot.start()
