from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import pyautogui


def scrape_with_selenium():
    cap = DesiredCapabilities().FIREFOX
    path = r"/Users/roberthughes/ds_projects/geckodriver"
    browser = webdriver.Firefox(capabilities=cap, executable_path=path)

    browser.get("https://pricerx.medispan.com/Refresh/login.aspx")
    delay = 5
    try:
        time.sleep(delay)
        # email_element = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, "emailInput")))
        # password_element = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, "passwordInput")))
        email_element = browser.find_element_by_id("emailInput")
        password_element = browser.find_element_by_id("passwordInput")
        email_element.send_keys("ajperea@tangcapital.com")
        password_element.send_keys("Tang123")
        login_button = browser.find_element_by_id("loginButton")
        # login_button = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, "loginButton")))
        login_button.click()

    except TimeoutException:
        print("Element couldn't be found")


def scrape_with_requests():
    import requests

    payload = {
        "emailInput": "ajperea@tangcapital.com",
        "passwordInput": "Tang123"
    }

    with requests.Session() as s:
        q = s.get("https://pricerx.medispan.com/Refresh/login.aspx")
        p = s.post("https://pricerx.medispan.com/Refresh/login.aspx", data=payload, cookies=q.cookies)
        print(p.cookies)
        print(p.text)

        r = s.get("https://pricerx.medispan.com/Refresh/Search.aspx", cookies=p.cookies)
        print(r.text)


if __name__ == "__main__":
    browser = scrape_with_selenium()
