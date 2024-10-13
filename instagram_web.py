#from selenium import webdriver as uc
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import time
import os
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import pyotp
import requests
import logging
import os, random
from urllib.parse import urlparse

logger = logging.getLogger('instagram_web')
handler = logging.StreamHandler() 
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

LOCATORS = {
    "cookie_pre_login_accept": "//button[text()='Decline optional cookies']",
    "login_username_field": "//input[@name='username']",
    "login_password_field": "//input[@name='password']",
    "login_error": "//p[@id='slfErrorAlert']",
    "login_sus_automated_dismiss":"//div/span[text()='Dismiss']",
    "login_edit_profile_btn":"//div/a[text()='Edit profile']",
    "login_profile_username":"//*[text()='{}']",
    "login_in_profile_btn":'//a[@tabindex="0" and text()="Log in"]',
    "login_sus_attempt":"//p[text()='Suspicious Login Attempt']",
    "login_save_info": "//button[text()='Save info']",
    "login_freezed":"//span[@dir='auto' and text()='Something went wrong']",


    "2f_screen_present": "//input[@aria-describedby='verificationCodeDescription' and @aria-label='Security Code']",
    "2f_entering_error": "//p[@id='twoFactorErrorAlert' and @role='alert']",



    "new_dm_btn": "//div[@role= 'button'][.//div//*//*[text()='New message']]",
    "dm_type_username": "//input[@placeholder='Search...']",
    "dm_select_user": '//div/span/span[text()="{}"]',
    "dm_start_chat_btn": "//div/div[text()='Chat' and @role='button']",
    "dm_msg_field": "//div[@role='textbox' and @aria-label='Message']",
    "dm_send_button": "//div[@role='button' and text()='Send']",
    "dm_error_present": "//*[@aria-label='Failed to send']",
    "dm_account_instagram_user":"//div[@role='presentation']//div//div//div//span[normalize-space(.)='Instagram User' and contains(@style, 'line-height: var(--base-line-clamp-line-height);')]",
    "dm_not_everyone":"//div//div//span[@dir='auto' and contains(text(),'Not everyone can message this account.')]",
    "dm_avatar_src":".//div[@role='presentation']//img[@alt='User avatar']",
    "dm_invite_sent":".//span[contains(text(), 'Invite sent')]",
    "dm_loaded":"//div//span[contains(text(),'Instagram') and @dir='auto']",
    "dm_already_sent": "//div[@role='none']//div[@dir='auto']",
    

    "dm_user_not_found": "//span[text()='No account found.']",

}
raw_string = r"This is a raw string: 'single quote' and \"double quote\"."


class WaitAndClickException(Exception):
    pass


class WaitException(Exception):
    pass


class BrokenChatException(Exception):
    pass


def ensure_logged(func):
    def wrapper(self, *args, **kwargs):
        if self.driver is None:
            logger.info("Web driver not initialized. Initializing now.")
            self.driver = self._init_driver()

        if not self.is_logged:
            logger.info("User is not logged in. Starting login process.")
            self.login()

        return func(self, *args, **kwargs)
    return wrapper


def escape_string_for_xpath(s):
    if '"' in s and "'" in s:
        return 'concat(%s)' % ", '\"',".join('"%s"' % x for x in s.split('"'))
    elif '"' in s:
        return "'%s'" % s
    return '"%s"' % s

class User:
    def __init__(self, profile_name=None, username=None, password=None, token=None, proxy=None,browser_executable_path=None,driver_executable_path=None,headless=False,log_path=None):
        self.cookies_dict = None
        self.profile_name = profile_name
        self.username = username
        self.password = password
        self.token = token
        self.proxy = proxy

        self.headless = headless
        self.browser_executable_path = browser_executable_path
        self.driver_executable_path = driver_executable_path

        self.is_logged = False
        self.driver = None

    
    def _init_driver(self):
        options = uc.ChromeOptions()

        if not os.path.exists(f"{os.getcwd()}/profiles"):
            os.makedirs(f"{os.getcwd()}/profiles")

        if self.profile_name:
            data_dir = f"{os.getcwd()}/profiles/{self.profile_name}"
            options.add_argument(f"--user-data-dir={data_dir}")
        options.add_argument("--lang=en_US")
        options.add_argument("--mute-audio")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument('--disable-infobars')
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-notifications")

        #proxy only without authentication
        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")
        if self.headless:
            options.add_argument('--headless=new')
        
        self.driver = uc.Chrome(options=options, browser_executable_path=self.browser_executable_path, driver_executable_path=self.driver_executable_path)
        return self.driver

    def __wait_and_click(self, xpath, time=5):
        logger.debug(f'__wait_and_click() - called with xpath: {xpath}, time: {time}')
        try:
            button = WebDriverWait(self.driver, time).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            button.location_once_scrolled_into_view
            button.click()
            logger.debug(f"Clicked the element with xpath: {xpath}")
        except Exception as e:
            logger.debug(f"Could not click the element with xpath: {xpath}. Error: {str(e)}")
            raise WaitAndClickException(f"Stopping execution due to failure to click on element: {xpath}") from e

    def __wait(self, xpath, time=5, webelement=""):
        logger.debug(f'__wait() - called with xpath: {xpath}, time: {time}')

        try:
            return WebDriverWait(self.driver if webelement == "" else webelement, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception as e:
            logger.debug(f"Could not wait for the element with xpath: {xpath}. Error: {e.msg}")
            raise WaitException(f"Stopping execution due to failure in waiting for element: {xpath}") from e

    def __wait_for_all(self, xpath, time=5):
        logger.debug(f'__wait_for_all() - called with xpath: {xpath}, time: {time}')

        try:
            return WebDriverWait(self.driver, time).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        except Exception as e:
            logger.debug(f"Could not wait for the element with xpath: {xpath}. Error: {str(e)}")
            raise WaitException(f"Stopping execution due to failure in waiting for element: {xpath}") from e

    def __is_element_present(self, xpath, time_to_wait=0, webelement="") -> bool:
        logger.debug(f"__is_element_present() called with parameters: xpath: {xpath} time to wait: {time_to_wait}")

        try:
            WebDriverWait(self.driver if webelement == "" else webelement, time_to_wait).until(EC.presence_of_element_located((By.XPATH, xpath)))
            logger.debug("__is_element_present() returning True")
            return True
        except:
            logger.debug("__is_element_present() returning False")
            return False

    def __paste_text(self, xpath, text, time_to_wait=0):
        logger.debug(f"__paste_text() called with xpath: {xpath}, text: {text}")

        action = ActionChains(self.driver)
        action.move_to_element(self.__wait(xpath, time_to_wait))
        action.click()
        action.send_keys(text)
        action.perform()

    def __wait_for_first_element_or_url(self, elements, timeout=5):
        """
        Check the current URL or wait for the first element from the list of xpaths to be present.

        :param elements: List of URLs or XPath locators.
        :param timeout: Maximum time to wait for the elements or URLs.
        :return: Index of the first element or URL that appears, or -1 if none appear.
        """
        logger.debug(f'wait_for_first_element_or_url() - called with elements: {str(elements)}, timeout: {timeout}')

        start_time = time.time()
        while time.time() - start_time < timeout:
            for index, element in enumerate(elements):
                time.sleep(0.05)
                try:
                    if element.startswith('http'):
                        if element in self.driver.current_url:
                            logger.debug(f"current URL matches with index: {index}")
                            return index
                    else:
                        WebDriverWait(self.driver, timeout=0).until(EC.presence_of_element_located((By.XPATH, element)))
                        logger.debug(f"found element with index: {index}")
                        return index
                except TimeoutException:
                    pass
                except Exception as e:
                    logger.debug(f"Error while waiting for the element or URL: {element}. Error: {str(e)}")

        logger.debug("No element or URL found/loaded within the timeout period.")
        return False

    def exit_driver(self):
        if self.driver != None:
            self.driver.quit()
        self.driver = None
        self.is_logged = False

    @ensure_logged
    def get_cookies(self, close_after=False):
        cookie = {}
        for c in self.driver.get_cookies():  
            cookie[c['name']] = c['value'] 

        self.cookies_dict = cookie
        if close_after:
            self.exit_driver()
        return cookie



    def __generate_2factor_code(self, token):
        totp = pyotp.TOTP(token)
        current_time = time.time()
        time_step = 30  # TOTP time step, usually 30 seconds
        remaining_time = time_step - (current_time % time_step)

        # If the code is valid for less than 5 seconds, wait for the next one
        if remaining_time < 4:
            time.sleep(remaining_time)

        new_code = totp.now()
        return new_code+"\n"

    def __accept_pre_login_cookie(self,sleep_time=2):
        logger.debug(f"__accept_pre_login_cookie() called")
        try:
            self.__wait_and_click(LOCATORS["cookie_pre_login_accept"], 2)
            logger.debug("Pre login cookie accepted")
            time.sleep(sleep_time)
            return True
        except WaitAndClickException:
            logger.warning("No pre login cookies to accept")
            return False

    def __two_factor(self):
        url = self.driver.current_url


        a = self.__wait(LOCATORS['2f_screen_present'],10)
        a.send_keys(Keys.CONTROL, 'a')
        a.send_keys(Keys.BACKSPACE)
        self.__paste_text(LOCATORS['2f_screen_present'], self.__generate_2factor_code(self.token), time_to_wait=10)

        

        if self.__is_element_present(LOCATORS['2f_entering_error'], 2):
            logger.error("2f_entering_error")
            sleep(5)
            self.__two_factor()

        for _ in range(10):
            if self.driver.current_url != url:
                return True
            sleep(1)

        logger.error("after entering code no change in url")
        return "login failed"


    def login(self):
        if self.driver == None:
            self.driver = self._init_driver()

        self.driver.get('https://www.instagram.com/direct/')
        if self.driver.current_url == 'https://www.instagram.com/direct/':
            self.is_logged = True
            return True            

        try:
            self.driver.get(f'https://instagram.com/{self.username}')

            self.__accept_pre_login_cookie()
            
            

            for _ in range(6):
                resp = self.__wait_for_first_element_or_url((
                    LOCATORS['2f_screen_present'],
                    LOCATORS['login_sus_automated_dismiss'],
                    LOCATORS['login_sus_attempt'],
                    LOCATORS["login_save_info"],
                    LOCATORS['login_profile_username'].format(self.username),
                    LOCATORS['login_error'],
                    LOCATORS['login_freezed']
                    ),30
                )
                if resp == 0:   #LOCATORS['2f_screen_present']
                    if self.__two_factor() == "login failed":
                        return "login failed"
                    continue
                elif resp == 1: #LOCATORS['login_sus_automated_dismiss']
                    logger.warning("Instagram: We suspect automated behavior on your account")
                    time.sleep(random.randrange(1,5))
                    self.__wait_and_click(LOCATORS['login_sus_automated_dismiss'],0)
                    time.sleep(random.randrange(1,5))
                    continue
                elif resp == 2: #LOCATORS["login_sus_attempt"]
                    logger.warning("Instagram: Suspicious Login Attempt")
                    return "Suspicious Login Attempt"
                elif resp == 3: #LOCATORS["login_save_info"]
                    self.__wait_and_click(LOCATORS["login_save_info"],0)
                    continue
                elif resp == 4: #LOCATORS['login_profile_username']
                    if self.__is_element_present(LOCATORS['login_edit_profile_btn']):
                        logger.info(f"Login succesfull to: {self.username}")
                        self.is_logged = True
                        return True
                    else:
                        if self.__is_element_present(LOCATORS['login_in_profile_btn'],0):
                            self.driver.get('https://instagram.com'+self.__wait(LOCATORS['login_in_profile_btn'],0).get_property('href'))
                            time.sleep(2)
                            self.__paste_text(LOCATORS["login_username_field"],self.username,1)
                            time.sleep(3)
                            self.__paste_text(LOCATORS["login_password_field"],self.password+'\n',1)
                            continue
                        logger.error(f"Login failed to: {self.username}")
                        return "login failed"
                elif resp == 5: #LOCATORS['login_error']
                    logger.error(f"There was a problem logger you into Instagram. Please try again soon.")
                    return "There was a problem logger you into Instagram. Please try again soon."
                elif resp == 6: #LOCATORS['login_freezed']
                    logger.error(f"Account is freezed: Rate limit reached")
                    return "Account is freezed: Rate limit reached"
                    
                        

                
            logger.error("login failed")
            return "login failed"
        except:
            logger.exception("login failed")
            return "login failed"


    def __get_photo_single_path(self,url):
        parsed_url = urlparse(url)
        path_without_params = parsed_url.path.split('?')[0]  # Splitting to remove parameters
        location = os.path.basename(path_without_params)
        logger.debug(f'extracted avatar src: {location}, full src: {url}')
        return location


    def __check_is_sent(self,msg):        
        res = self.__wait_for_first_element_or_url([
            LOCATORS['dm_error_present'],
            "//div[@role='none']//div[@dir='auto' and text()="+escape_string_for_xpath(msg)+"]",
            LOCATORS['dm_invite_sent'],
            LOCATORS['dm_not_everyone']
        ],timeout=5)

        if res == 0:
            if self.__is_element_present(LOCATORS["dm_account_instagram_user"],0):
                return 'account not found'
            return "account freezed"
        elif res == 1:
            return
        elif res == 2:
            return 'invite already sent'
        elif res == 3:
            return "not everyone can message this account"
         

    @ensure_logged
    def send_msg_to_msg_id(self,msg_id,msg,skip_if_already_messaged=False):
        def load_chat():
            self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')
            try:
                self.__wait(LOCATORS['dm_loaded'],15)
            except WaitException:
                if self.__is_element_present(LOCATORS["dm_account_instagram_user"],0):
                    return 'msg_id acc not found'
                logger.error('chat didnt loaded in time... trying again')
                self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')
                try:
                    self.__wait(LOCATORS['dm_loaded'],15)
                except WaitException:
                    logger.error('chat didnt loaded 2 consecutive times')
                    return 'error'
        

        logger.debug(f'send_msg_to_msg_id() - called with arguments: msg_id: {msg_id}, msg: {msg}, check_dm_message: {skip_if_already_messaged}')
        
        err = load_chat()
        if err:
            return err

        if skip_if_already_messaged and self.__is_element_present(LOCATORS['dm_already_sent']):
            return 'already sent'

        
        resp = self.__wait_for_first_element_or_url([
            LOCATORS["dm_msg_field"],
            LOCATORS["dm_not_everyone"],
            LOCATORS['dm_invite_sent'],
            ],20)
        if resp == 0:
            msg_field = self.__wait(LOCATORS["dm_msg_field"],0)
        elif resp == 1:
            return "not everyone can message this account"
        elif resp == 2:
            return 'invite already sent'
        elif resp == False:
            logger.error(f'dm page is not loading or unexpected message not yet known. Please contact maintainer to fix that')
            return 'error'
            
        err = self.__paste_msg_in_dm(msg,msg_field)
        if err:
            return err

        time.sleep(3)
        err = self.__check_is_sent(msg)
        if err:
            return err
  
        return "sent" 


    @ensure_logged
    def send_msg(self, to_username, msg, skip_if_already_messaged=False):
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=1, i',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Chromium";v="129", "Not=A?Brand";v="8"',
            'sec-ch-ua-full-version-list': '"Chromium";v="129.0.6668.70", "Not=A?Brand";v="8.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"15.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'x-asbd-id': '129477',
            'x-ig-app-id': '936619743392459',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        url = "https://www.instagram.com/api/v1/users/web_profile_info/"
        params = {"username": to_username}
        self.get_cookies(close_after=False)
        response = requests.get(url, params=params, cookies=self.cookies_dict, headers=headers)

        if response.status_code == 404:
            logger.info(f"account: {to_username} not found")
            return "account not found"
        
        msg_id = response.json()['data']['user']['eimu_id']
        logger.info(msg_id)
        
        return self.send_msg_to_msg_id(msg_id, msg, skip_if_already_messaged)



    def __paste_msg_in_dm(self,msg,msg_field):
        try:
            action = ActionChains(self.driver)
            action.move_to_element(msg_field)
            action.click()
            action.pause(1)
            action.send_keys(msg.replace('\n',''))
            action.perform()
            time.sleep(1)

            try:
                self.__wait_and_click(LOCATORS['dm_send_button'],5)
            except WaitAndClickException:
                if self.__is_element_present(LOCATORS["dm_not_everyone"],0):
                    return "not everyone can message this account"
        except StaleElementReferenceException:
            if self.__is_element_present(LOCATORS["dm_invite_sent"],0):
                return 'invite already sent'
            elif self.__is_element_present(LOCATORS["dm_not_everyone"],0):
                return "not everyone can message this account"
            logger.error("Msg field loaded but something unexpected is obstructing it. Please contact maintainer to fix that")
            return 'error'
        