from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

def create_firefox_driver():
    options = Options()
    #options.add_argument('--headless')
    options.set_preference("intl.accept_languages", "en-US") # Specify the language code

    driver = webdriver.Firefox(options=options)
    return driver

def initialize_driver():
    driver = create_firefox_driver()
    wait = WebDriverWait(driver, 10)
    return driver, wait
