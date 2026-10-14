import time
import random
import re
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
XPATH_INPUT_FIELD        = "//android.widget.EditText"
XPATH_CONFIRM_CREATION   = "//*[@text='Confirm creation']"
XPATH_START_BTN          = "//*[@text='Start']"
XPATH_LINK_NOW_BTN       = "//*[@text='Link now']"
XPATH_CONFIRM_BINDING    = "//*[@text='Confirm binding']"
XPATH_IN_PROGRESS        = "//*[@text='In progress']"
XPATH_HOME_TAB           = "//*[@text='Home']" 

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

def hide_keyboard(driver):
    try:
        driver.hide_keyboard()
        log("kbd", "✅ Hid on-screen keyboard")
    except Exception:
        pass
    time.sleep(2.0)

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

def extract_identity_code(driver):
    log("extract", "Waiting for identity screen to render...")
    time.sleep(3)
    elements = driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
    log("extract", f"Found {len(elements)} TextView(s) on screen. Scanning...")
    candidates = []
    for el in elements:
        try:
            text = el.text.strip()
            if not text:
                continue
            candidates.append(text)
            if len(text) >= 32 and re.fullmatch(r"[0-9a-fA-F]+", text):
                log("extract", f"✅ Found identity code candidate: {text[:8]}...")
                return text
        except Exception:
            continue
    log("extract", "⚠️ No hex identity found. All TextViews on screen were:")
    for c in candidates:
        log("extract", f"    -> '{c[:80]}' (len={len(c)})")
    fallback = [c for c in candidates if len(c) >= 40]
    if fallback:
        longest = max(fallback, key=len)
        log("extract", f"⚠️ Using fallback (longest string): {longest[:8]}...")
        return longest
    raise Exception("Could not find identity code on screen.")

# ============================================================
#   REGISTRATION FLOW (9 Steps)
# ============================================================
def run_registration(driver):
    wait = WebDriverWait(driver, 25)

    # 1. Generate Identity
    log("1/9", "Clicking 'Generate identity ID'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_GENERATE))).click()
    log("1/9", "✅ Clicked")
    random_sleep()

    # 2. Extract Identity
    log("2/9", "Extracting identity code...")
    identity_code = extract_identity_code(driver)
    log("2/9", f"✅ Identity: {identity_code[:8]}...")

    # 3. Save & Next
    log("3/9", "Clicking 'I saved it, next'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_SAVED))).click()
    log("3/9", "✅ Clicked")
    random_sleep(3.0, 5.0)

    # 4. Verify Identity & Confirm Creation
    log("4/9", "Waiting for 'Verify identity ID backup' screen...")
    login_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
    login_input.click()
    human_type(login_input, identity_code)
    log("4/9", "✅ Typed identity code")
    random_sleep(0.5, 1.5)

    hide_keyboard(driver)

    log("4/9", "Clicking 'Confirm creation'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_CONFIRM_CREATION))).click()
    log("4/9", "✅ Confirm creation clicked")

    # 5. Wait for Cloudflare Turnstile (If it appears)
    log("5/9", "Waiting for Cloudflare Human verification...")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//*[@text='Home']"))
        )
        log("5/9", "✅ Cloudflare passed, dashboard loaded!")
    except TimeoutException:
        log("5/9", "⚠️ Cloudflare verification seems stuck. Dumping page source...")
        print(driver.page_source, flush=True)
        raise Exception("Cloudflare verification failed or took too long.")

    random_sleep(4.0, 7.0)

    # 6. Click Start & Handle Referral Popup
    log("6/9", "Clicking 'Start' button to trigger referral popup...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_START_BTN))).click()
    log("6/9", "✅ Start clicked. Waiting for 'Referral code not linked' popup...")
    random_sleep(3.0, 5.0)

    log("6/9", "Clicking 'Link now' button...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_LINK_NOW_BTN))).click()
    log("6/9", "✅ Link now clicked")
    random_sleep(3.0, 5.0)

    # 7. Bind Referral Code
    log("7/9", "Binding referral code...")
    referral_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
    referral_input.click()
    human_type(referral_input, REFERRAL_CODE)
    log("7/9", "✅ Typed referral code")
    random_sleep(0.5, 1.5)

    hide_keyboard(driver)

    log("7/9", "Clicking 'Confirm binding'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_CONFIRM_BINDING))).click()
    log("7/9", "✅ Confirm binding clicked")
    random_sleep(3.0, 5.0)

    # 8. Navigate back to Home tab
    log("8/9", "Navigating back to Home tab...")
    home_tab = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_HOME_TAB)))
    home_tab.click()
    log("8/9", "✅ Home tab clicked")
    random_sleep(2.0, 4.0)

    # 9. Click Start and Verify
    log("9/9", "Clicking 'Start' button on Home screen...")
    start_btn = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_START_BTN)))
    start_btn.click()
    log("9/9", "✅ Start button clicked. Waiting for 'In progress'...")
    random_sleep(3.0, 5.0)

    try:
        wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_IN_PROGRESS)))
        log("9/9", "✅ Success verified (In progress)")
    except TimeoutException:
        log("9/9", "⚠️ 'In progress' text not detected, saving anyway.")

    with open(FILE_NAME, "a") as file:
        file.write(f"{identity_code}\n")
    log("9/9", f"💾 Saved to {FILE_NAME}")

# ============================================================
#   MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = APP_PACKAGE
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
