import time
import random
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
#   CONFIGURATION
# ============================================================
FILE_NAME = "identities.txt"

# UI Elements
XPATH_WELCOME_LOGIN_LINK = "//*[@text='Log in']"
XPATH_INPUT_FIELD        = "//android.widget.EditText"
XPATH_LOGIN_BTN          = "//android.widget.Button[@text='Log in']"
ID_START_BTN             = "com.siriusnetwork.app:id/btn_start_link"

# ============================================================
#   HELPERS
# ============================================================
def random_sleep(min_s=2.0, max_s=5.0):
    time.sleep(random.uniform(min_s, max_s))

def human_type(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.1, 0.3))

def farm_account(driver, identity_code):
    wait = WebDriverWait(driver, 20)
    print(f"🚜 Farming account: {identity_code[:8]}...")

    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_WELCOME_LOGIN_LINK))).click()
    random_sleep()

    identity_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))
    identity_input.click()
    human_type(identity_input, identity_code)
    random_sleep(0.5, 1.5)

    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_LOGIN_BTN))).click()
    print("   -> Logged in.")
    random_sleep(4.0, 8.0)

    start_btn = wait.until(EC.element_to_be_clickable((AppiumBy.ID, ID_START_BTN)))
    start_btn.click()
    print("   -> 🟢 Clicked Start! Points generating.")
    random_sleep(3.0, 5.0)

# ============================================================
#   MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    try:
        with open(FILE_NAME, "r") as file:
            all_accounts = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print("No identities found. Run register.py first.")
        exit(0)

    if not all_accounts:
        print("No valid identities found.")
        exit(0)

    # Shuffle to simulate human randomness
    random.shuffle(all_accounts)

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = "com.siriusnetwork.app"
    options.app_activity = ".MainActivity"
    options.full_reset = False

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    try:
        for account in all_accounts:
            driver.execute_script("mobile: clearApp", {"appId": "com.siriusnetwork.app"})
            driver.activate_app("com.siriusnetwork.app")
            random_sleep(3.0, 6.0)
            try:
                farm_account(driver, account)
            except Exception as e:
                print(f"   -> ❌ Failed to farm: {e}")
            # Human break between accounts
            random_sleep(8.0, 15.0)
    finally:
        driver.quit()
