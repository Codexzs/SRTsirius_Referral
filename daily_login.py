import time
import random
import subprocess
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
#   CONFIGURATION
# ============================================================
FILE_NAME = "identities.txt"
APP_PACKAGE = "com.siriusnetwork.app"

XPATH_WELCOME_LOGIN_LINK = "//*[@text='Log in']"
XPATH_INPUT_FIELD        = "//android.widget.EditText"
XPATH_LOGIN_BTN          = "//android.widget.Button[@text='Log in']"
ID_START_BTN             = "com.siriusnetwork.app:id/btn_start_link"

# ============================================================
#   HELPERS
# ============================================================
def log(step, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{step}] {msg}", flush=True)

def random_sleep(min_s=2.0, max_s=5.0):
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

def farm_account(driver, identity_code):
    wait = WebDriverWait(driver, 20)
    log("farm", f"🚜 Farming account: {identity_code[:8]}...")

    log("farm", "Clicking Log in link...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_WELCOME_LOGIN_LINK))).click()
    random_sleep()

    log("farm", "Entering identity code...")
    identity_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
    identity_input.click()
    human_type(identity_input, identity_code)
    random_sleep(0.5, 1.5)

    log("farm", "Clicking Log in button...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_LOGIN_BTN))).click()
    log("farm", "✅ Logged in")
    random_sleep(4.0, 8.0)

    log("farm", "Clicking Start...")
    start_btn = wait.until(EC.element_to_be_clickable((AppiumBy.ID, ID_START_BTN)))
    start_btn.click()
    log("farm", "🟢 Clicked Start!")
    random_sleep(3.0, 5.0)

# ============================================================
#   MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    try:
        with open(FILE_NAME, "r") as file:
            all_accounts = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        log("init", "No identities found. Run register.py first.")
        exit(0)

    if not all_accounts:
        log("init", "No valid identities found.")
        exit(0)

    log("init", f"Loaded {len(all_accounts)} accounts. Shuffling...")
    random.shuffle(all_accounts)

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
        for idx, account in enumerate(all_accounts, 1):
            log("main", f"=== Farming {idx}/{len(all_accounts)}: {account[:8]}... ===")
            reset_app()
            try:
                farm_account(driver, account)
            except Exception as e:
                log("main", f"❌ Failed to farm: {e}")
            random_sleep(8.0, 15.0)
    finally:
        driver.quit()
        log("init", "Driver session closed")
