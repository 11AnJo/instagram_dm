from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
import logging
import sys

logger = logging.getLogger(__name__)
#logging.basicConfig(filename='dm.log', level=logging.WARNING,
#                    format='%(asctime)s %(levelname)s: %(message)s',
#                    datefmt='%m/%d/%Y %I:%M:%S %p',
#                    handlers=[logging.FileHandler('example.log'), logging.StreamHandler(sys.stdout)])

selectors = {
            "cookie_accept":"//button[text()='Only allow essential cookies']",
            "cookie_text":"//*[text()='Allow the use of cookies from Instagram on this browser?']",
            "login_username_field":"//input[@name='username']",
            "login_password_field":"//input[@name='password']",
            "profile_message_button":"//div[@role='button' and text()='Message']",
            "profile_followers_div":"//div[text()=' followers']",
            "dm_msg_field":"//textarea[@placeholder='Message...']",
            "dm_notification_present":"//h2[text()='Turn on Notifications']",
            "dm_notification_disable":"//button[text()='Not Now']",
            "dm_send_button":"//button[@type='button' and text()='Send']"
        }


def initialize_driver(path_to_firefox='C:\Program Files\Mozilla Firefox\Firefox.exe',debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('log.txt')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.debug('initialize_driver() called with debug=%s', debug) 

    try:
        binary = FirefoxBinary(path_to_firefox)
        logger.debug(f"setting up firefox in a {path_to_firefox} path")

        profile = FirefoxProfile()
        profile.set_preference("javascript.enabled", True)

        options = Options()
        options.set_preference("intl.accept_languages", "en-US") # Specify the language code

        #options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1") # Specify the iPhone user-agent string
        driver = webdriver.Firefox(firefox_binary=binary, firefox_profile=profile,options=options)
        global wait
        wait = WebDriverWait(driver, 10)
        __accept_cookie(driver)
        return driver

    except:
        logger.exception("initialize_driver")


def __is_element_present(driver, xpath):
    logger.debug(f"__is_element_present() called with parameters: driver={driver}, xpath={xpath}")
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        logger.debug("__is_element_present() returned False")
        return False
    logger.debug("__is_element_present() returned True")
    return True


def __accept_cookie(driver):
    logger.debug(f"__accept_cookie() called with parameters: driver={driver}" )
    try:
        driver.get('https://instagram.com/')
        if wait.until(EC.presence_of_element_located((By.XPATH, selectors["cookie_text"]))):
            driver.find_element_by_xpath(selectors["cookie_accept"]).click()
            sleep(2)
        else:
            logger.warning("No cookies to accept!")
    except:
        logger.exception("__accept_cookie")


def login(driver, username, password):
    logger.debug(f"login() called with parameters: driver={driver}, username={username}, password={password}")
    try:
        driver.get('https://instagram.com/login')
        username_field = wait.until(EC.presence_of_element_located((By.XPATH, selectors["login_username_field"])))
        password_field = driver.find_element_by_xpath(selectors["login_password_field"])
        url = driver.current_url
        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        
        #wait for instagram to login
        while True:
            if driver.current_url != url:
                logger.info(f"Login succesfull to {username}")
                return 
            sleep(1)

    except:
        logger.exception("login")
            

def send_msg(driver,to_username,msg):
    logger.debug(f"send_msg() called with parameters: driver={driver}, to_username={to_username}, msg={msg}")
    #logger.info(f"{to_username} : {msg}")
    try:
        driver.get(f"https://www.instagram.com/{to_username}")
        try:
            msg_btn = wait.until(EC.presence_of_element_located((By.XPATH, selectors["profile_message_button"])))
        except:
            logger.warning(f"cannot send message to user:{to_username}")
            return

        msg_btn.click()
        
        #in the direct messages section
        msg_field = wait.until(EC.presence_of_element_located((By.XPATH,selectors["dm_msg_field"])))

        msg_field.send_keys(msg)

        if __is_element_present(driver, selectors["dm_notification_present"]):
            notifications = driver.find_element_by_xpath(selectors["dm_notification_disable"])
            notifications.click()

        send_btn = driver.find_element_by_xpath(selectors["dm_send_button"])
        send_btn.click()
        logger.info(f"send {msg} to {to_username}")
    except:
        logger.exception("send_msg")