from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium import webdriver

from typing import Optional
from pathlib import Path
from time import sleep
import time
import json
import requests
import logging
import random
from functools import wraps

from .constants import URLS, LOCATORS
from .utils import escape_string_for_xpath, generate_2factor_code, generate_uuid
from .selenium_utils import SeleniumUtils, ProxyUtils, WaitAndClickException, WaitException

logger = logging.getLogger('instagram_web')
handler = logging.StreamHandler() 
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)




class BrokenChatException(Exception):
    pass


def logged_in(func):
    def wrapper(self, *args, **kwargs):
        if self.driver is None:
            logger.info("Web driver not initialized. Initializing now.")
            self.driver = self.init_driver()

        if not self.is_logged_in:
            logger.info("User is not logged in. Starting login process.")
            self.login()

        return func(self, *args, **kwargs)
    return wrapper


def cache_cookies():
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            current_time = time.time()
            
            # If we have cached cookies and they're still fresh
            if (self._session_cookies and 
                self._cookies_last_fetched and 
                (current_time - self._cookies_last_fetched) < 12 * 3600):   #12 hrs
                return self._session_cookies
                
            # Otherwise fetch fresh cookies
            result = func(self, *args, **kwargs)
            self._cookies_last_fetched = current_time
            return result
        return wrapper
    return decorator

class Session(SeleniumUtils):
    def __init__(
            self,
            profile_name: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            token: Optional[str] = None,
            proxy: Optional[str] = None,
            browser_executable_path: Optional[Path] = None,
            driver_executable_path: Optional[Path] = None,
            headless: bool = False
        ) -> None:        
        self._username = username
        self._password = password
        self._token = token

        self._proxy = proxy
        self.proxy_utils = ProxyUtils() if proxy else None
        self._profile_name = profile_name

        self.is_logged_in = False
        self._session_cookies = None

        self.driver = None
        self._headless = headless
        self._browser_executable_path = browser_executable_path
        self._driver_executable_path = driver_executable_path

    def init_driver(self):
        if self.driver:
            self.driver.quit()

        options = webdriver.ChromeOptions()
        service = webdriver.ChromeService(executable_path=self._driver_executable_path)
        
        if self.proxy_utils:
            plugin = self.proxy_utils.create_proxy_extension(self._proxy)
            options.add_extension(plugin)
        
        self.configure_browser_options(
            options=options,
            browser_executable_path=self._browser_executable_path,
            profile_name=self._profile_name,
            headless=self._headless
        )

        self.driver = webdriver.Chrome(options=options, service=service)

        if self.proxy_utils:
            self.proxy_utils.cleanup_proxy_extension()
        return self.driver

    def exit_driver(self):
        if self.driver != None:
            self.driver.quit()
        self.driver = None
        self.is_logged_in = False

    @logged_in
    @cache_cookies()
    def get_cookies(self, close_after=False):
        """Get cookies from the browser and cache them for 12 hours"""
        self._session_cookies = {}
        for c in self.driver.get_cookies():  
            self._session_cookies[c['name']] = c['value'] 
        if close_after:
            self.exit_driver()
        return self._session_cookies

    def _accept_pre_login_cookie(self,sleep_time=2):
        logger.debug(f"_accept_pre_login_cookie() called")
        try:
            self._wait_and_click(LOCATORS['login']["cookie_pre_login_accept"], 2)
            logger.debug("Pre login cookie accepted")
            time.sleep(sleep_time)
            return True
        except WaitAndClickException:
            logger.warning("No pre login cookies to accept")
            return False

    def _two_factor(self):
        logger.debug(f"_two_factor() called")
        url = self.driver.current_url

        a = self._wait(LOCATORS['login']['2f_screen_present'],10)
        a.send_keys(Keys.CONTROL, 'a')
        a.send_keys(Keys.BACKSPACE)
        self._paste_text(LOCATORS['login']['2f_screen_present'], generate_2factor_code(self._token), timeout=10, press_enter=True)

        if self._is_element_present(LOCATORS['login']['2f_entering_error'], 2):
            logger.error("2f_entering_error")
            sleep(5)
            self._two_factor()

        for _ in range(10):
            if self.driver.current_url != url:
                return True
            sleep(1)

        logger.error("after entering code no change in url")
        return "login failed"


    def login(self):
        if self.driver is None:
            self.init_driver()

        self.driver.get(URLS['login'])
        if self.driver.current_url == 'https://www.instagram.com/direct/':
            self.is_logged_in = True
            return True

        try:
            self._accept_pre_login_cookie()
            time.sleep(1)
            self._paste_text(LOCATORS["login"]["username_field"],self._username,1)
            time.sleep(1)
            self._paste_text(LOCATORS["login"]["password_field"],self._password+'\n',1)

            for _ in range(6):
                resp = self._wait_for_first_element_or_url((
                    LOCATORS['login']['2f_screen_present'],
                    LOCATORS['login']['sus_automated_dismiss'],
                    LOCATORS['login']['suspicious_attempt'],
                    LOCATORS['login']["save_info"],
                    LOCATORS['login']['profile_username'].format(self._username),
                    LOCATORS['login']['error'],
                    LOCATORS['login']['freezed']
                    ),30
                )
                if resp == 0:   #LOCATORS['2f_screen_present']
                    if self._two_factor() == "login failed":
                        return "login failed"
                    continue

                elif resp == 1: #LOCATORS['login_sus_automated_dismiss']
                    logger.warning("Instagram: We suspect automated behavior on your account")
                    time.sleep(random.randrange(1,5))
                    self._wait_and_click(LOCATORS['login']['sus_automated_dismiss'],0)
                    time.sleep(random.randrange(1,5))
                    continue
                
                elif resp == 2: #LOCATORS["login_sus_attempt"]
                    logger.warning("Instagram: Suspicious Login Attempt")
                    return "Suspicious Login Attempt"
                
                elif resp == 3: #LOCATORS["login_save_info"]
                    self._wait_and_click(LOCATORS['login']["save_info"],0)
                    continue

                elif resp == 4: #LOCATORS['login_profile_username']
                    logger.info(f"Login succesfull to: {self._username}")
                    self.is_logged_in = True
                    return True
                    
                elif resp == 5: #LOCATORS['login_error']
                    logger.error(f"There was a problem logger you into Instagram. Please try again soon.")
                    return "There was a problem logger you into Instagram. Please try again soon."
                
                elif resp == 6: #LOCATORS['login_freezed']
                    logger.error(f"Account is freezed: Rate limit reached")
                    return "Account is freezed: Rate limit reached"
                elif resp == -1:
                    break   
                        
            logger.error("login failed")
            return "login failed"
        except:
            logger.exception("login failed")
            return "login failed"


    def _check_is_sent(self,msg):
        res = self._wait_for_first_element_or_url([
            LOCATORS['dm']['error_present'],
            "//div[@role='none']//div[@dir='auto' and text()="+escape_string_for_xpath(msg)+"]",
            LOCATORS['dm']['invite_sent'],
            LOCATORS['dm']['not_everyone']
        ],timeout=5)

        if res == 0:
            if self._is_element_present(LOCATORS['dm']["account_instagram_user"],0):
                return 'account not found'
            return "account freezed"
        elif res == 1:
            return
        elif res == 2:
            return 'invite already sent'
        elif res == 3:
            return "not everyone can message this account"

    def _paste_msg_in_dm(self,msg,msg_field):
        try:
            action = ActionChains(self.driver)
            action.move_to_element(msg_field)
            action.click()
            action.pause(1)
            action.send_keys(msg.replace('\n',''))
            action.perform()
            time.sleep(1)

            try:
                self._wait_and_click(LOCATORS['dm']['send_button'],5)
            except WaitAndClickException:
                if self._is_element_present(LOCATORS['dm']["not_everyone"],0):
                    return "not everyone can message this account"
                
        except StaleElementReferenceException:
            if self._is_element_present(LOCATORS['dm']["invite_sent"],0):
                return 'invite already sent'
            
            elif self._is_element_present(LOCATORS['dm']["not_everyone"],0):
                return "not everyone can message this account"
            
            logger.error("Msg field loaded but something unexpected is obstructing it. Please contact maintainer to fix that")
            return 'error'
          

    @logged_in
    def send_msg_to_msg_id(self,msg_id,msg,skip_if_already_messaged=False):
        logger.debug(f'send_msg_to_msg_id() - called with arguments: msg_id: {msg_id}, msg: {msg}, check_message: {skip_if_already_messaged}')
        
        self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')
        try:
            self._wait(LOCATORS['dm']['loaded'],10)
        except WaitException:
            if self._is_element_present(LOCATORS['dm']["account_instagram_user"],0):
                return 'msg_id acc not found'
            
            logger.error('chat didnt loaded in time... trying again')
            self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')
            try:
                self._wait(LOCATORS['dm']['loaded'],10)
            except WaitException:
                logger.error('chat didnt loaded 2 consecutive times')
                return 'error'

        if skip_if_already_messaged and self._is_element_present(LOCATORS['dm']['already_sent']):
            return 'message already sent'

        
        resp = self._wait_for_first_element_or_url([
            LOCATORS['dm']["msg_field"],
            LOCATORS['dm']["not_everyone"],
            LOCATORS['dm']['invite_sent'],
            ],20)
        if resp == 0:
            msg_field = self._wait(LOCATORS['dm']["msg_field"],0)
        elif resp == 1:
            return "not everyone can message this account"
        elif resp == 2:
            return 'invite already sent'
        elif resp == False:
            logger.error(f'dm page is not loading or unexpected message not yet known. Please contact maintainer to fix that')
            return 'error'
            
        err = self._paste_msg_in_dm(msg,msg_field)
        if err:
            return err

        time.sleep(3)
        err = self._check_is_sent(msg)
        if err:
            return err
  
        return "sent"


    @logged_in
    def send_msg(self, to_username, msg, skip_if_already_messaged=False):
        data = self.get_user_info(to_username)
        if data == "account not found":
            return "account not found"
        elif data == "error":
            return "error"
        
        msg_id = data['data']['user']['eimu_id']
        
        return self.send_msg_to_msg_id(msg_id, msg, skip_if_already_messaged)


    @logged_in
    def get_user_info(self, username):
        headers = {
            'accept': '/',
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

        params = {"username": username}
        
        response = requests.get(URLS['user_info_endpoint'], params=params, cookies=self.get_cookies(), headers=headers)

        if response.status_code == 404:
            logger.info(f"account: {username} not found")
            return "account not found"
        elif response.status_code != 200:
            logger.error(f"Error while fetching user id. Status code: {response.status_code}")
            return "error"
        
        try:
            #msg_id = response.json()['data']['user']['eimu_id']
            return response.json()
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response")
            return "error"
    
    @logged_in
    def get_posts_from_hashtag(self, hashtag, max_id=None, rank_token=None, enable_metadata=False):
        headers = {
            'accept': '/',
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

        params = {
            'enable_metadata': str(enable_metadata).lower(),
            'query': '#' + hashtag,
            'next_max_id': max_id,
            'rank_token': rank_token if rank_token else generate_uuid(),
        }

        response = requests.get(
            URLS['hashtag_search_endpoint'],
            params=params,
            cookies=self.get_cookies(),
            headers=headers,
        )

        if response.status_code != 200:
            logger.error(f"Error while fetching posts from hashtag. Status code: {response.status_code}")
            return "error"
        
        try:
            data = response.json()
            next_max_id = data['media_grid']['next_max_id']
            rank_token = data['media_grid']['rank_token']
            return data, next_max_id, rank_token
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response")
            return "error"
