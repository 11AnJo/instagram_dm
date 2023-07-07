from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def create_firefox_driver():
    path_to_firefox = r'C:\Program Files\Mozilla Firefox\Firefox.exe'

    options = Options()
    #options.add_argument('--headless')
    options.set_preference("intl.accept_languages", "en-US") # Specify the language code
    options.binary_location = path_to_firefox

    driver = webdriver.Firefox(options=options)
    return driver


def initialize_driver():
    driver = create_firefox_driver()
    wait = WebDriverWait(driver, 5)
    return driver, wait
