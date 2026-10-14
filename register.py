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
XPATH_CLOUDFLARE_CHECK   = "//*[@text='Human verification']"

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

def is_app_alive(driver):
    """Returns True if the app is still in the foreground."""
    for xpath in [
        "//*[@text='Home']",
        "//*[@text='Human verification']",
        "//*[contains(@text, 'Checking')]",
        "//*[contains(@text, 'Generate')]",
        "//*[contains(@text, 'identity')]",
    ]:
        try:
            driver.find_element(AppiumBy.XPATH, xpath)
            return True
        except Exception:
            continue
    return False

def wait_for_cloudflare(driver, max_wait=120):
    log("cf", f"Waiting up to {max_wait}s for Cloudflare to auto-pass...")
    start = time.time()
    while time.time() - start < max_wait:
        elapsed = int(time.time() - start)

        try:
            driver.find_element(AppiumBy.XPATH, "//*[@text='Home']")
            log("cf", f"✅ Cloudflare passed after {elapsed}s!")
            return True
        except Exception:
            pass

        # Detect app crash
        if not is_app_alive(driver):
            log("cf", f"❌ App appears to have crashed at {elapsed}s (foreground is no longer the app)")
            return False

        if elapsed > 0 and elapsed % 15 == 0:
            log("cf", f"   [{elapsed}s] Still waiting...")

        time.sleep(3)

    log("cf", f"❌ Cloudflare did NOT auto-pass within {max_wait}s")
    return False

# ============================================================
#   REGISTRATION FLOW
# ============================================================
def run_registration(driver):
    wait = WebDriverWait(driver, 25)

    log("1/9", "Clicking 'Generate identity ID'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_GENERATE))).click()
    log("1/9", "✅ Clicked")
    random_sleep()

    log("2/9", "Extracting identity code...")
    identity_code = extract_identity_code(driver)
    log("2/9", f"✅ Identity: {identity_code[:8]}...")

    log("3/9", "Clicking 'I saved it, next'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_SAVED))).click()
    log("3/9", "✅ Clicked")
    random_sleep(3.0, 5.0)

    log("4/9", "Typing identity code on verify screen...")
    login_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
    login_input.click()
    human_type(login_input, identity_code)
    log("4/9", "✅ Typed identity code")
    random_sleep(0.5, 1.5)
    hide_keyboard(driver)

    log("4/9", "Clicking 'Confirm creation'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_CONFIRM_CREATION))).click()
    log("4/9", "✅ Confirm creation clicked")

    # ---- Cloudflare wait with retry ----
    log("5/9", "Waiting for Cloudflare Human verification...")
    if not wait_for_cloudflare(driver, max_wait=120):
        log("5/9", "❌ Cloudflare is blocking. Dumping page source...")
        print(driver.page_source, flush=True)
        raise Exception("Cloudflare verification is blocking the workflow. "
                        "Ask mentor to disable Cloudflare on staging.")

    random_sleep(4.0, 7.0)

    log("6/9", "Clicking Start to trigger referral popup...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_START_BTN))).click()
    log("6/9", "✅ Start clicked, waiting for popup...")
    random_sleep(3.0, 5.0)

    log("6/9", "Clicking 'Link now'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_LINK_NOW_BTN))).click()
    log("6/9", "✅ Link now clicked")
    random_sleep(3.0, 5.0)

    log("7/9", "Binding referral code...")
    referral_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
    referral_input.click()
    human_type(referral_input, REFERRAL_CODE)
    log("7/9", "✅ Typed referral code")
    random_sleep(0.5, 1.5)
    hide_keyboard(driver)

    log("7/9", "Clicking 'Confirm binding'...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_CONFIRM_BINDING))).click()
    log("7/9", "✅ Referral bound")
    random_sleep(3.0, 5.0)

    log("8/9", "Navigating to Home tab...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_HOME_TAB))).click()
    log("8/9", "✅ Home tab clicked")
    random_sleep(2.0, 4.0)

    log("9/9", "Clicking Start on Home screen...")
    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_START_BTN))).click()
    log("9/9", "✅ Start clicked")
    random_sleep(3.0, 5.0)

    try:
        wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_IN_PROGRESS)))
        log("9/9", "✅ Success verified (In progress)")
    except TimeoutException:
        log("9/9", "⚠️ 'In progress' not detected, saving anyway.")

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
