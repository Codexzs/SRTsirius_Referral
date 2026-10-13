import time
import random
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
ACCOUNTS_PER_RUN = 1   # ⬅️ CHANGED: 1 account per run = 1 fresh GitHub IP

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
def random_sleep(min_s=2.0, max_s=4.0):
    time.sleep(random.uniform(min_s, max_s))

def human_type(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.1, 0.3))

# ============================================================
#   REGISTRATION FLOW
# ============================================================
def run_registration(driver):
    wait = WebDriverWait(driver, 25)

    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_GENERATE))).click()
    random_sleep()

    identity_code = wait.until(EC.presence_of_element_located(
        (AppiumBy.XPATH, XPATH_IDENTITY)
    )).text.strip()
    print(f"      Generated Identity: {identity_code[:8]}...")

    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_BTN_SAVED))).click()
    random_sleep(3.0, 5.0)

    # Login
    try:
        login_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD))
        )
    except TimeoutException:
        wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_WELCOME_LOGIN_LINK))).click()
        random_sleep()
        login_input = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, XPATH_INPUT_FIELD)))

    login_input.click()
    human_type(login_input, identity_code)
    random_sleep(0.5, 1.5)

    wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, XPATH_LOGIN_BTN))).click()
    random_sleep(4.0, 7.0)

    # Bind referral
    wait.until(EC.element_to_be_clickable((AppiumBy.ID, ID_START_LINK_BTN))).click()
    random_sleep()

    referral_input = wait.until(EC.presence_of_element_located((AppiumBy.ID, ID_REFERRAL_INPUT)))
    referral_input.click()
    human_type(referral_input, REFERRAL_CODE)
    wait.until(EC.element_to_be_clickable((AppiumBy.ID, ID_BIND_BTN))).click()
    random_sleep(2.0, 4.0)

    # Save
    try:
        wait.until(EC.presence_of_element_located((AppiumBy.ID, ID_SUCCESS_MSG)))
        print("      ✅ Success verified.")
    except TimeoutException:
        print("      ⚠️ Success msg not found. Saving anyway.")

    with open(FILE_NAME, "a") as file:
        file.write(f"{identity_code}\n")
    print(f"      💾 Saved to {FILE_NAME}")

# ============================================================
#   MAIN
# ============================================================
if __name__ == "__main__":
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = "com.siriusnetwork.app"
    options.app_activity = ".MainActivity"
    options.full_reset = False

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    try:
        for i in range(ACCOUNTS_PER_RUN):
            print(f"\n=== Creating Account {i+1}/{ACCOUNTS_PER_RUN} ===")
            driver.execute_script("mobile: clearApp", {"appId": "com.siriusnetwork.app"})
            driver.activate_app("com.siriusnetwork.app")
            random_sleep(3.0, 6.0)
            try:
                run_registration(driver)
            except Exception as e:
                print(f"❌ Failed: {e}")
    finally:
        driver.quit()
