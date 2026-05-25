import os
import sys
import gc
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
#                   REALTIME LOGGING
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
        self.messages = []

        self.target_uid = ""
        self.haters_name = ""

        self.current_cookie_index = 0
        self.message_index = 0

        # =================================================
        #               STABLE SETTINGS
        # =================================================

        self.delay = 25

        self.cleanup_interval = 5

        self.cookie_rotation_interval = 10

        self.driver_restart_interval = 40

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
    #               MEMORY CLEANUP
    # =====================================================

    def cleanup_memory(self):

        try:

            self.driver.execute_script("""
                window.localStorage.clear();
                window.sessionStorage.clear();
            """)

            gc.collect()

            success("MEMORY CLEANED")

        except:
            pass

    # =====================================================
    #               SOFT REFRESH
    # =====================================================

    def soft_refresh_chat(self):

        try:

            info("REFRESHING CHAT")

            self.driver.refresh()

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                60
            )

            if not loaded:

                return False

            time.sleep(3)

            success("CHAT REFRESHED")

            return True

        except Exception as e:

            error(f"REFRESH FAILED : {e}")

            return False

    # =====================================================
    #               AUTO LOAD FILES
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
                    open(
                        "time.txt",
                        "r"
                    ).read().strip()
                )

            if (
                not self.cookies_list
                or not self.target_uid
                or not self.messages
            ):

                raise Exception(
                    "FILES EMPTY OR MISSING"
                )

            success(
                "ALL FILES AUTO LOADED"
            )

            log(
                f"[CONFIG] "
                f"[COOKIES: {len(self.cookies_list)}] "
                f"[MESSAGES: {len(self.messages)}] "
                f"[DELAY: {self.delay}s]"
            )

            return True

        except Exception as e:

            error(f"AUTO LOAD FAILED : {e}")

            return False

    # =====================================================
    #               DRIVER SETUP
    # =====================================================

    def setup_driver(self):

        try:

            options = Options()

            # =================================================
            #               STABLE HEADLESS
            # =================================================

            options.add_argument("--headless=new")

            options.add_argument("--no-sandbox")

            options.add_argument(
                "--disable-dev-shm-usage"
            )

            options.page_load_strategy = "eager"

            # =================================================
            #               MEMORY FIXES
            # =================================================

            options.add_argument(
                "--disable-renderer-backgrounding"
            )

            options.add_argument(
                "--disable-background-timer-throttling"
            )

            options.add_argument(
                "--disable-backgrounding-occluded-windows"
            )

            options.add_argument(
                "--memory-pressure-off"
            )

            options.add_argument(
                "--max_old_space_size=128"
            )

            options.add_argument("--js-flags=--expose-gc")

            options.add_argument("--disable-gpu")

            options.add_argument("--disable-dev-tools")

            options.add_argument("--no-first-run")

            options.add_argument("--disable-extensions")

            options.add_argument("--disable-popup-blocking")

            options.add_argument("--disable-notifications")

            options.add_argument("--disable-sync")

            options.add_argument("--disable-translate")

            options.add_argument("--disable-infobars")

            options.add_argument("--disable-default-apps")

            options.add_argument(
                "--disable-component-update"
            )

            options.add_argument(
                "--disable-breakpad"
            )

            options.add_argument(
                "--disable-background-networking"
            )

            options.add_argument(
                "--disable-hang-monitor"
            )

            options.add_argument(
                "--disable-ipc-flooding-protection"
            )

            options.add_argument(
                "--disable-client-side-phishing-detection"
            )

            options.add_argument(
                "--disable-software-rasterizer"
            )

            options.add_argument(
                "--disable-blink-features=AutomationControlled"
            )

            options.add_argument("--no-zygote")

            options.add_argument("--single-process")

            options.add_argument("--window-size=1280,720")

            # =================================================
            #               CACHE DISABLE
            # =================================================

            options.add_argument("--disk-cache-size=0")

            options.add_argument("--media-cache-size=0")

            options.add_argument(
                "--disable-application-cache"
            )

            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "disk-cache-size": 0
            }

            options.add_experimental_option(
                "prefs",
                prefs
            )

            # =================================================
            #               LOG REDUCTION
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

            return True

        except Exception as e:

            error(f"DRIVER ERROR : {e}")

            return False

    # =====================================================
    #               DRIVER RESTART
    # =====================================================

    def restart_driver(self):

        try:

            info("RESTARTING DRIVER")

            try:

                self.driver.quit()

            except:
                pass

            time.sleep(5)

            if not self.setup_driver():

                return False

            current_cookie = (
                self.current_cookie_index
                % len(self.cookies_list)
            )

            if not self.switch_cookie(
                current_cookie
            ):

                return False

            success("DRIVER RESTARTED")

            return True

        except Exception as e:

            error(f"RESTART FAILED : {e}")

            return False

    # =====================================================
    #               GET MESSAGE BOX
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
    #               COOKIE SWITCH
    # =====================================================

    def switch_cookie(self, cookie_no):

        try:

            cookie_str = self.cookies_list[cookie_no]

            info(
                f"SWITCHING COOKIE #{cookie_no + 1}"
            )

            self.driver.get(
                "https://www.facebook.com"
            )

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                60
            )

            if not loaded:

                raise Exception(
                    "FACEBOOK LOAD FAILED"
                )

            self.driver.delete_all_cookies()

            self.driver.execute_script("""
            window.localStorage.clear();
            window.sessionStorage.clear();
            """)

            time.sleep(2)

            cookies = cookie_str.split(";")

            added = 0

            for cookie in cookies:

                if "=" not in cookie:
                    continue

                try:

                    name, value = cookie.strip().split(
                        "=",
                        1
                    )

                    self.driver.add_cookie({
                        "name": name,
                        "value": value,
                        "domain": ".facebook.com"
                    })

                    added += 1

                except:
                    pass

            success(
                f"COOKIE LOADED : {added}"
            )

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

                raise Exception(
                    "CHAT LOAD FAILED"
                )

            box = self.get_message_box()

            if not box:

                raise Exception(
                    "MESSAGE BOX FAILED"
                )

            success(
                f"COOKIE #{cookie_no + 1} ACTIVE"
            )

            return True

        except Exception as e:

            error(f"COOKIE SWITCH FAILED : {e}")

            return False

    # =====================================================
    #               SEND MESSAGE
    # =====================================================

    def send_message(self, text):

        try:

            if not self.driver_alive():

                return False

            box = self.get_message_box()

            if not box:

                raise Exception(
                    "MESSAGE BOX NOT FOUND"
                )

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

            time.sleep(1)

            # =================================================
            #               FINAL MESSAGE
            # =================================================

            final_msg = (
                f"{self.haters_name} {text}"
            ).strip()

            # =================================================
            #               CLEAR BOX
            # =================================================

            box.send_keys(
                Keys.CONTROL,
                "a"
            )

            time.sleep(0.5)

            box.send_keys(
                Keys.BACKSPACE
            )

            time.sleep(1)

            # =================================================
            #               REGET BOX
            # =================================================

            box = self.driver.find_element(
                By.XPATH,
                "//div[@contenteditable='true']"
            )

            # =================================================
            #               HUMAN TYPE
            # =================================================

            for char in final_msg:

                box.send_keys(char)

                time.sleep(
                    random.uniform(
                        0.01,
                        0.04
                    )
                )

            # =================================================
            #               STABILITY WAIT
            # =================================================

            time.sleep(
                random.uniform(
                    1.5,
                    2.5
                )
            )

            # =================================================
            #               SEND
            # =================================================

            box.send_keys(Keys.ENTER)

            # =================================================
            #               POST WAIT
            # =================================================

            time.sleep(
                random.uniform(
                    2,
                    3
                )
            )

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
    #                   START
    # =====================================================

    def start(self):

        info("LOADING CONFIG")

        if not self.auto_load():

            return

        if not self.setup_driver():

            return

        if not self.switch_cookie(0):

            return

        success("MESSAGE SENDING STARTED")

        count = 0

        while True:

            try:

                # =============================================
                #           DRIVER HEALTH
                # =============================================

                if not self.driver_alive():

                    restarted = self.restart_driver()

                    if not restarted:

                        time.sleep(10)

                    continue

                # =============================================
                #           SWITCH COOKIE EVERY MESSAGE
                # =============================================

                current_cookie = (
                    self.current_cookie_index
                    % len(self.cookies_list)
                )

                switched = self.switch_cookie(
                    current_cookie
                )

                if not switched:

                    self.current_cookie_index += 1

                    continue

                # =============================================
                #           GET MESSAGE
                # =============================================

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

                # =============================================
                #           LOGS
                # =============================================

                log(
                    f"[MSG #{count}] "
                    f"[COOKIE #{current_cookie + 1}] "
                    f"[TIME: {current_time}] "
                    f"[STATUS: {status}] "
                    f"[MESSAGE: {short_msg}]"
                )

                log(
                    "────────────────────────────────────────"
                )

                # =============================================
                #           NEXT MESSAGE
                # =============================================

                self.message_index += 1

                # =============================================
                #           CLEANUP
                # =============================================

                if (
                    count %
                    self.cleanup_interval
                    == 0
                ):

                    self.cleanup_memory()

                    self.soft_refresh_chat()

                # =============================================
                #           DRIVER RESTART
                # =============================================

                if (
                    count %
                    self.driver_restart_interval
                    == 0
                ):

                    self.restart_driver()

                # =============================================
                #           NEXT COOKIE
                # =============================================

                self.current_cookie_index += 1

                # =============================================
                #           DELAY
                # =============================================

                for _ in range(self.delay):

                    time.sleep(1)

                    if not self.driver_alive():

                        break

            except Exception as e:

                error(f"MAIN LOOP ERROR : {e}")

                self.restart_driver()

                time.sleep(5)


# =========================================================
#                       RUN
# =========================================================

if __name__ == "__main__":

    bot = FacebookMessenger()

    bot.start()
