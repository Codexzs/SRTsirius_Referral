import time
import random
import subprocess
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ============================================================
#   CONFIGURATION
# ============================================================
REFERRAL_CODE = "wQhGMG"
FILE_NAME = "identities.txt"
ACCOUNTS_PER_RUN = 1
APP_PACKAGE = "com.siriusnetwork.app"

# ============================================================
#   UI ELEMENTS
# ============================================================
XPATH_BTN_GENERATE       = "//*[@text='Generate identity ID']"
XPATH_BTN_SAVED          = "//*[@text='I saved it, next']"
XPATH_WELCOME_LOGIN_LINK = "//*[@text='Log in']"
XPATH_INPUT_FIELD        = "//android.widget.EditText"
XPATH_LOGIN_BTN          = "//android.widget.Button[@text='Log in']"
XPATH_IDENTITY           = "//android.widget.Button[@text='Copy']/parent::*/android.widget.TextView"

ID_START_LINK_BTN = "com.siriusnetwork.app:id/btn_start_link"
ID_REFERRAL_INPUT = "com.siriusnetwork.app:id/et_referral_code"
ID_BIND_BTN       = "com.siriusnetwork.app:id/btn_bind_referral"
ID_SUCCESS_MSG    = "com.siriusnetwork.app:id/tv_success_message"

# ============================================================
#   HELPERS
# ============================================================
def log(step, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{step}] {msg}", flush=True)

def random_sleep(min_s=2.0, max_s=4.0):
    time.sleep(random.uniform(min_s, max_s))

def human_type(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.1, 0.3))

def reset_app():
    log("reset", "Force-stopping app...")
    subprocess.run(["adb", "shell", "am", "force-stop", APP_PACKAGE])
    time.sleep(1)
    log("reset", "Clearing app data...")
    subprocess.run(["adb", "shell", "pm", "clear", APP_PACKAGE])
    time.sleep(2)
    log("reset", "Relaunching app...")
    subprocess.run([
        "adb", "shell", "monkey",
        "-p", APP_PACKAGE,
        "-c", "android.intent.category.LAUNCHER",
        "1"
    ], capture_output=True)
    time.sleep(3)
    log("reset", "✅ App reset complete")

# ============================================================
#   REGISTRATION FLOW
# ============================================================
def run_registration(driver):
    wait = WebDriverWait(driver, 25)

    log("1/6", "Clicking 'Generate identity ID'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_GENERATE))).click()
    log("1/6", "✅ Clicked")
    random_sleep()

    log("2/6", "Reading identity code...")
    identity_code = wait.until(EC.presence_of_element_located(
        (AppiumBy.XPATH, XPATH_IDENTITY)
    )).text.strip()
    log("2/6", f"✅ Read identity: {identity_code[:8]}...")

    log("3/6", "Clicking 'I saved it, next'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_SAVED))).click()
    log("3/6", "✅ Clicked")
    random_sleep(3.0, 5.0)

    log("4/6", "Navigating to login screen...")
    try:
        login_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD))
        )
        log("4/6", "✅ Already on Import screen")
    except TimeoutException:
        log("4/6", "On Welcome screen, clicking Log in link...")
        wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_WELCOME_LOGIN_LINK))).click()
        random_sleep()
        login_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
        log("4/6", "✅ Navigated to Import screen")

    login_input.click()
    human_type(login_input, identity_code)
    log("4/6", "✅ Typed identity code")
    random_sleep(0.5, 1.5)

    log("5/6", "Clicking Log in button...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_LOGIN_BTN))).click()
    log("5/6", "✅ Logged in")
    random_sleep(4.0, 7.0)

    log("6/6", "Binding referral code...")
    wait.until(EC.element_to_be_clickable((AppiumBy.ID, ID_START_LINK_BTN))).click()
    random_sleep()

    referral_input = wait.until(EC.presence_of_element_located((AppiumBy.ID, ID_REFERRAL_INPUT)))
    referral_input.click()
    human_type(referral_input, REFERRAL_CODE)
    wait.until(EC.element_to_be_clickable((AppiumBy.ID, ID_BIND_BTN))).click()
    log("6/6", "✅ Referral submitted")
    random_sleep(2.0, 4.0)

    try:
        wait.until(EC.presence_of_element_located((AppiumBy.ID, ID_SUCCESS_MSG)))
        log("6/6", "✅ Success message verified")
    except TimeoutException:
        log("6/6", "⚠️ Success msg not detected, saving anyway")

    with open(FILE_NAME, "a") as file:
        file.write(f"{identity_code}\n")
    log("6/6", f"💾 Saved to {FILE_NAME}")

# ============================================================
#   MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = APP_PACKAGE
    options.app_activity = ".MainActivity"
    options.full_reset = False

    log("init", "Connecting to Appium server...")
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    log("init", "✅ Appium session created")

    try:
        for i in range(ACCOUNTS_PER_RUN):
            log("main", f"=== Creating Account {i+1}/{ACCOUNTS_PER_RUN} ===")
            reset_app()
            try:
                run_registration(driver)
            except Exception as e:
                log("main", f"❌ Failed: {e}")
    finally:
        driver.quit()
        log("init", "Driver session closed")
