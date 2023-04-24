from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary



def create_firefox_driver():
    options = Options()
    #options.add_argument('--headless')
    options.set_preference("intl.accept_languages", "en-US") # Specify the language code
    
    path_to_firefox = 'C:\Program Files\Mozilla Firefox\Firefox.exe'
    binary = FirefoxBinary(path_to_firefox)

    driver = webdriver.Firefox(options=options,firefox_binary=binary)
    return driver


def initialize_driver():
    driver = create_firefox_driver()
    wait = WebDriverWait(driver, 10)
    return driver, wait

