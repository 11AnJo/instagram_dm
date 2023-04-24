from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

def create_chrome_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=en-US')
    
    driver = webdriver.Chrome(options=options)
    return driver

def initialize_driver():
    driver = create_chrome_driver()
    wait = WebDriverWait(driver, 10)
    return driver, wait
