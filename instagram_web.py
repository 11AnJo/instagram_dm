#from selenium import webdriver as uc
from undetected_chromedriver import Chrome as uc
from selenium.webdriver.chrome.options import Options
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
import re
import logging
import os
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

def initialize_log(name_of_log, debug=False):
    """
    Initialize a logger with two file handlers: one for normal logs and one for debug logs.
    The debug log file is limited to 1MB in size.
    """

    # Create the log directory if it doesn't exist
    log_dir = f'./app/log/{name_of_log}'
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)


    # Initialize the logger
    logger = logging.getLogger(name_of_log)
    logger.setLevel(logging.DEBUG)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create file handler for normal logging
    normal_log_file = os.path.join(log_dir, f"{name_of_log}.log")
    file_handler = logging.FileHandler(normal_log_file)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create file handler for debug logging with rotation
    debug_log_file = os.path.join(log_dir, f"{name_of_log}-debug.log")
    debug_file_handler = RotatingFileHandler(debug_log_file, maxBytes=1*1024*1024, backupCount=5)
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    logger.addHandler(debug_file_handler)

    # Stream handler to output to console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

LOCATORS = {
    "cookie_pre_login_accept": "//button[text()='Decline optional cookies']",
    "cookie_post_login_accept": "//div//span[text()='Decline optional cookies']",

    "cookie_accept": "//button[text()='Decline optional cookies']",

    "cookie_text": "//*[text()='Allow the use of cookies from Instagram on this browser?']",
    "login_username_field": "//input[@name='username']",
    "login_password_field": "//input[@name='password']",
    "new_dm_btn": "//div[@role= 'button'][.//div//*//*[text()='New message']]",
    "dm_type_username": "//input[@placeholder='Search...']",
    "dm_select_user": '//div/span/span[text()="{}"]',
    "dm_user_not_found": "//span[text()='No account found.']",
    "dm_start_chat_btn": "//div/div[text()='Chat' and @role='button']",
    "dm_msg_field": "//div[@role='textbox' and @aria-label='Message']",
    "dm_notification_disable": "//button[text()='Not Now']",
    "dm_send_button": "//div[@role='button' and text()='Send']",
    "dm_error_present": "//*[@aria-label='Failed to send']",
    "dm_account_instagram_user":"//div[@role='presentation']//div//div//div//span[normalize-space(.)='Instagram User' and contains(@style, 'line-height: var(--base-line-clamp-line-height);')]",
    "dm_not_everyone":"//div//div//span[@dir='auto' and contains(text(),'Not everyone can message this account.')]",
    "dm_avatar_src":".//div[@role='presentation']//img[@alt='User avatar']",
    "dm_is_sent":".//div[@role='listitem']//img[contains (@src, '{}')]",
    "dm_invite_sent":".//span[contains(text(), 'Invite sent')]",
    "dm_loading":"//div[@aria-label='Loading...']//div//img",
    "dm_loaded":"//div//span[contains(text(),'Instagram') and @dir='auto']",
    "2f_screen_present": "//input[@aria-describedby='verificationCodeDescription' and @aria-label='Security Code']",
    "2f_entering_error": "//p[@id='twoFactorErrorAlert' and @role='alert']",
    "dm_already_sent": "//div[@role='none']//div[@dir='auto']",
    "login_error": "//p[@id='slfErrorAlert']",
    "sus_attempt":"//p[text()='Suspicious Login Attempt']",
    "save_login_info": "//button[text()='Save info']",

}


class WaitAndClickException(Exception):
    pass


class WaitException(Exception):
    pass


class BrokenChatException(Exception):
    pass


def ensure_logged(func):
    def wrapper(self, *args, **kwargs):
        if self.driver is None:
            self.logger.info("driver not active")
            self.driver = self._init_driver()

        if not self.is_logged:
            self.logger.info("login not active")
            self.login()

        return func(self, *args, **kwargs)
    return wrapper




class User:
    def __init__(self, profile_name=None, username=None, password=None, token=None, debug=False, starting_page='https://www.instagram.com/direct/',proxy=None,browser_executable_path=None,driver_executable_path=None):
        self.cookies_dict = None
        self.profile_name = profile_name
        self.username = username
        self.password = password
        self.token = token
        self.starting_page = starting_page
        self.is_logged = False
        self.proxy = proxy

        self.dm_notification_disabled = False

        self.debug = debug
        self.logger = initialize_log(f"IG_{profile_name}_{username}",self.debug)

        self.browser_executable_path = browser_executable_path
        self.driver_executable_path = driver_executable_path

        self.driver = None

    
    def _init_driver(self):
        print(self.proxy)
        options = Options()
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
        #options.add_argument('--headless=new')
        #options.add_experimental_option('excludeSwitches', ['enable-logging']) not working in undetected crhome
        
        self.driver = uc(options=options, browser_executable_path=self.browser_executable_path, driver_executable_path=self.driver_executable_path)
        return self.driver

    def __wait_and_click(self, xpath, time=5):
        self.logger.debug(
            f'__wait_and_click() - called with xpath: {xpath}, time: {time}')
        try:
            button = WebDriverWait(self.driver, time).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            button.location_once_scrolled_into_view
            button.click()
            self.logger.debug(f"Clicked the element with xpath: {xpath}")
        except Exception as e:
            self.logger.debug(
                f"Could not click the element with xpath: {xpath}. Error: {str(e)}")
            raise WaitAndClickException(
                f"Stopping execution due to failure to click on element: {xpath}") from e

    def __wait(self, xpath, time=5, webelement=""):
        self.logger.debug(
            f'__wait() - called with xpath: {xpath}, time: {time}')

        try:
            return WebDriverWait(self.driver if webelement == "" else webelement, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception as e:
            self.logger.debug(
                f"Could not wait for the element with xpath: {xpath}. Error: {e.msg}")
            raise WaitException(
                f"Stopping execution due to failure in waiting for element: {xpath}") from e

    def __wait_for_all(self, xpath, time=5):
        self.logger.debug(
            f'__wait_for_all() - called with xpath: {xpath}, time: {time}')

        try:
            return WebDriverWait(self.driver, time).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        except Exception as e:
            self.logger.debug(
                f"Could not wait for the element with xpath: {xpath}. Error: {str(e)}")
            raise WaitException(
                f"Stopping execution due to failure in waiting for element: {xpath}") from e

    def __is_element_present(self, xpath, time_to_wait=0, webelement="") -> bool:
        self.logger.debug(
            f"__is_element_present() called with parameters: xpath: {xpath} time to wait: {time_to_wait}")

        wait = WebDriverWait(self.driver if webelement == "" else webelement, time_to_wait)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.logger.debug("__is_element_present() returning True")
            return True
        except:
            self.logger.debug("__is_element_present() returning False")
            return False

    def __paste_text(self, xpath, text, time_to_wait=0):
        self.logger.debug(
            f"__paste_text() called with xpath: {xpath}, text: {text}")

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
        self.logger.debug(f'wait_for_first_element_or_url() - called with elements: {elements}, timeout: {timeout}')

        start_time = time.time()
        while time.time() - start_time < timeout:
            for index, element in enumerate(elements):
                try:
                    if element.startswith('http'):
                        if element in self.driver.current_url:
                            self.logger.debug(f"current URL matches with index: {index}")
                            return index
                        time.sleep(0.05)
                    else:
                        WebDriverWait(self.driver, timeout=0.05).until(EC.presence_of_element_located((By.XPATH, element)))
                        self.logger.debug(f"found element with index: {index}")
                        return index
                except TimeoutException:
                    pass  # Ignore timeout and check the next element or URL
                except Exception as e:
                    self.logger.debug(f"Error while waiting for the element or URL: {element}. Error: {str(e)}")

        self.logger.debug("No element or URL found/loaded within the timeout period.")
        return False


    @ensure_logged
    def get_suggestions(self, username):
        def get_all_usernames():
            usernames = set()
            repeated_count = 0
            threshold = 5  # Adjust the threshold as needed

            while True:
                elements = self.__wait_for_all('//a//div//span//div')
                old_len = len(usernames)
                for el in elements:
                    try:
                        # Get the text of the element
                        text = el.text

                        # Skip if the username contains 'Verified'
                        if 'Verified' in text:
                            continue

                        # Add the username to the set
                        usernames.add(text)
                    except StaleElementReferenceException:
                        continue

                if old_len == len(usernames):
                    repeated_count += 1
                    if repeated_count >= threshold:
                        break
                else:
                    repeated_count = 0

                # Scroll down to load more usernames
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", elements[-1])
                time.sleep(1)  # Adjust the sleep time as needed

            return usernames

        LOCATORS_SUGGESTIONS = {
            'page_unavailable': "//span[text()='Sorry, this page isn't available.']",
            'suggest_button': "//div[@role='button']//div//*[local-name() = 'svg']",
            'see_all_button': "//a[@role='link']//span[@dir='auto' and text()='See all']",
            'similar_acc_presence': "//div[text()='Discover more accounts']",
            'err_unable_to_load': "//div[text()='Unable to load suggestions.']"
        }

        try:

            self.logger.debug(
                f"get_suggestions() - called with username: {username}")

            self.driver.get(f'https://www.instagram.com/{username}')
            try:
                self.__wait_and_click(LOCATORS_SUGGESTIONS['suggest_button'])
            except WaitAndClickException:
                if self.__is_element_present(LOCATORS_SUGGESTIONS["page_unavailable"]):
                    self.logger.debug("Profile is unavailable")
                    return "Profile is unavailable"
                self.logger.exception("AJAJ")

            if self.__is_element_present(LOCATORS_SUGGESTIONS['err_unable_to_load'], 3):
                return 'acc locked'

            self.__wait_and_click(LOCATORS_SUGGESTIONS['see_all_button'])

            self.__wait(LOCATORS_SUGGESTIONS['similar_acc_presence'])
            return get_all_usernames()

        except WaitAndClickException as e:
            self.logger.error(
                f"get_suggestions() - Stopping execution. Error: {str(e)}")
            return False
        except WaitException as e:
            self.logger.error(
                f"get_suggestions() - Stopping execution. Error: {str(e)}")
            return False

    def exit_driver(self):
        if self.driver != None:
            self.driver.quit()
        self.driver = None
        self.is_logged = False
        self.dm_notification_disabled = False

    @ensure_logged
    def get_cookies(self, close_after=True):

        def transform_cookies(cookies):
            headers = {}
            cookie_str = ""
            for cookie in cookies:
                cookie_str += cookie['name'] + "=" + cookie['value'] + "; "
            # remove the last semicolon and space
            headers["Cookie"] = cookie_str[:-2]
            # <---------------------
            headers["X-Ig-App-Id"] = "936619743392459"
            return headers

        try:

            cookies = self.driver.get_cookies()
            cookies_dict = transform_cookies(cookies)
            if close_after:
                self.exit_driver()

            self.cookies_dict = cookies_dict
            return cookies_dict
        except:
            self.logger.exception("get_cookies")

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

    def __accept_pre_login_cookie(self):
        self.logger.debug(f"__accept_pre_login_cookie() called")
        try:
            self.__wait_and_click(LOCATORS["cookie_pre_login_accept"], 2)
            self.logger.debug("Pre login cookie accepted")
            time.sleep(1)
            return True
        except WaitAndClickException:
            self.logger.debug("No pre login cookies to accept")
            return False

    def __accept_post_login_cookie(self,time_to_wait=2):
        self.logger.debug(f"__accept_post_login_cookie() called")
        try:
            self.__wait_and_click(LOCATORS["cookie_post_login_accept"], time_to_wait)
            self.logger.debug("Post login cookie accepted")
            time.sleep(2)
            return True
        except WaitAndClickException:
            self.logger.debug("No post login cookies to accept")
            return False

    def __two_factor(self):
        url = self.driver.current_url
        self.logger.debug("looking for 2f")
        try:
            a = self.__wait(LOCATORS['2f_screen_present'],10)
            a.send_keys(Keys.CONTROL, 'a')
            a.send_keys(Keys.BACKSPACE)
            self.__paste_text(LOCATORS['2f_screen_present'], self.__generate_2factor_code(
                self.token), time_to_wait=10)

        except WaitException:
            self.logger.info("2factor not found")
            return True

        if self.__is_element_present(LOCATORS['2f_entering_error'], 2):
            self.logger.error("2f_entering_error")
            sleep(5)
            self.__two_factor()

        for _ in range(10):
            if self.driver.current_url != url:
                return True

            sleep(1)
        self.logger.error("after entering code no change in url")
        return "cannot login"

    def login(self):
        if self.driver == None:
            self.driver = self._init_driver()

        self.driver.get('https://www.instagram.com/direct/')
        if self.driver.current_url == 'https://www.instagram.com/direct/':
            self.is_logged = True
            return True

        if self.username == None or self.password == None:
            self.driver.get('https://instagram.com/accounts/login')

            self.logger.info(
                "Username and password not specified. Please login by yourself")
            while True:
                sleep(0.5)
                if "instagram.com/accounts/onetap" in self.driver.current_url:
                    try:
                        self.__wait_and_click(LOCATORS["save_login_info"],20)
                    except WaitAndClickException:
                        if self.__is_element_present(LOCATORS['sus_attempt']):
                            self.logger.warning("suspicious login attempt")
                            input("suspicious login attempt")

                    sleep(5)


                    try:
                        self.__wait_and_click(LOCATORS["dm_notification_disable"], 3)
                        self.dm_notification_disabled = True
                    except WaitAndClickException:
                        self.logger.info("No dm notification")

                    #self.driver.get("https://www.instagram.com/direct/inbox")
                    sleep(1)


                    self.logger.info(f"Login succesfull to {self.username}")
                    self.is_logged = True
                    return True

        try:
            self.driver.get('https://instagram.com/accounts/login')

            self.__accept_pre_login_cookie()
            time.sleep(3)
            self.__paste_text(LOCATORS["login_username_field"],self.username,1)
            time.sleep(3)
            self.__paste_text(LOCATORS["login_password_field"],self.password+'\n',1)


            # self.__paste_text(LOCATORS["login_username_field"],self.username,1)
            # self.__paste_text(LOCATORS["login_password_field"],self.password)

            if self.__is_element_present(LOCATORS['login_error'], 2):
                self.logger.error(
                    f"There was a problem logging you into Instagram. Please try again soon.")
                return "There was a problem logging you into Instagram. Please try again soon."

            if self.token:
                self.logger.debug("two factor is on, trying to login")
                self.__two_factor()

                
            try:
                self.__accept_post_login_cookie()
                self.__wait(LOCATORS["save_login_info"],15)
                time.sleep(2)

                self.__wait_and_click(LOCATORS["save_login_info"],1)
                while True:
                    if "https://www.instagram.com/accounts/onetap" in self.driver.current_url:
                        time.sleep(1)
                        continue
                    time.sleep(2)
                    break
            except WaitAndClickException:
                if self.__is_element_present(LOCATORS['sus_attempt']):
                    self.logger.warning("suspicious login attempt")
                    return "suspicious login attempt"

        
            if self.__accept_post_login_cookie(0):
                self.logger.warning("post cookie not accepted first time, please adjust the sleep time")

            try:
                self.__wait_and_click(LOCATORS["dm_notification_disable"], 10)
                self.dm_notification_disabled = True
            except WaitAndClickException:
                self.logger.info("No dm notification")

            #self.driver.get("https://www.instagram.com/direct/inbox")
            sleep(10)
            self.logger.info(f"Login succesfull to")
            self.is_logged = True
            return True

        except:
            self.logger.exception("login")

    def __get_id_from_url(self,url):
        self.logger.debug(f"__get_id_from_url() called with: url: {url}")
        match = re.search(r"https://www\.instagram\.com/direct/t/(\d+)/", url)
        if match:
            message_id = match.group(1)
            self.logger.debug(f"Message ID: {message_id}")
            return message_id
        else:
            self.logger.debug("Message ID not found in the current URL")
            return False

    def __get_photo_single_path(self,url):
        parsed_url = urlparse(url)
        path_without_params = parsed_url.path.split('?')[0]  # Splitting to remove parameters
        location = os.path.basename(path_without_params)
        self.logger.debug(f'extracted avatar src: {location}, full src: {url}')
        return location


    def __check_is_sent(self):
        
        if not self.__is_element_present(LOCATORS['dm_already_sent'], 10):
            return 'message is not even appearing'

        try:
            avatar_src = self.__get_photo_single_path(self.__wait(LOCATORS['dm_avatar_src'],5).get_attribute("src"))
        except WaitException:
            self.logger.error("Cannot locate dm name")
            return "Cannot locate dm name"
        
        res = self.__wait_for_first_element_or_url([
            LOCATORS['dm_error_present'],
            LOCATORS['dm_is_sent'].format(avatar_src)
        ],timeout=20)

        if res == 0:
            if self.__is_element_present(LOCATORS["dm_account_instagram_user"],0):
                return 'msg_id acc not found'
            return "freeze"
        elif res == 1:
            return
         
            



    @ensure_logged
    def send_msg_to_msg_id(self,msg_id,msg,skip_if_already_messaged=False):
        def load_chat():
            self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')
            try:
                self.__wait(LOCATORS['dm_loaded'],15)
            except WaitException:
                if self.__is_element_present(LOCATORS["dm_account_instagram_user"],0):
                    return 'msg_id acc not found'
                self.logger.error('chat didnt loaded in time... trying again')
                self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')
                try:
                    self.__wait(LOCATORS['dm_loaded'],15)
                except WaitException:
                    self.logger.error('chat didnt loaded 2 consecutive times')
                    return 'error'
        

        self.logger.debug(f'send_msg_to_msg_id() - called with arguments: msg_id: {msg_id}, msg: {msg}, check_dm_message: {skip_if_already_messaged}')
        
        err = load_chat()
        if err:
            return err

        if skip_if_already_messaged and self.__is_element_present(LOCATORS['dm_already_sent']):
            return 'already sent'

            

        resp = self.__wait_for_first_element_or_url([
            LOCATORS["dm_msg_field"],
            LOCATORS["dm_not_everyone"],
            LOCATORS['dm_invite_sent'],
            ],10)
        
        if resp == 0:
            msg_field = self.__wait(LOCATORS["dm_msg_field"],0)
        elif resp == 1:
            return "not everyone"
        elif resp == 2:
            return 'invite already sent'
        elif resp == False: 
            self.logger.error(f'dm page is not loading or unexpected message not yet known. Please contact maintainer to fix that')
            return 'error'

        
            
        

        if self.dm_notification_disabled == False:
            self.__check_dm_notification()
            
        err = self.__paste_msg_in_dm(msg,msg_field)
        if err:
            return err 

        err = self.__check_is_sent()
        if err:
            return err
  
        return "sent" 




    @ensure_logged
    def send_msg(self, to_username, msg, skip_if_already_messaged=False):
        def go_to_user_dm():
            if not self.__is_element_present(LOCATORS["new_dm_btn"], 0):
                self.driver.get("https://www.instagram.com/direct/")

            if self.dm_notification_disabled == False:
                self.__check_dm_notification()

            try:
                self.__wait_and_click(LOCATORS["new_dm_btn"])
            except:
                self.driver.get("https://www.instagram.com/direct/")
                self.__wait_and_click(LOCATORS["new_dm_btn"])

            search_user_field = self.__wait(LOCATORS["dm_type_username"])
            search_user_field.send_keys(to_username)
            username_path = LOCATORS["dm_select_user"].format(to_username)

            try:
                self.__wait_and_click(username_path)
            except:
                self.logger.error("cant select user from list")
                return "No account found."
            
            next_btn = self.__wait(LOCATORS["dm_start_chat_btn"])
            last_url = self.driver.current_url
            self.driver.execute_script("arguments[0].click();", next_btn)

            tries = 0
            changed = False
            while tries < 50:
                sleep(0.5)
                if last_url == self.driver.current_url:
                    tries += 1
                    continue
                else:
                    changed = True
                    break
            if changed == False:
                self.logger.error("cant access the new url")
                return "url problem"
            
        def load_chat():
            err = go_to_user_dm()
            if err:
                return err
            try:
                self.__wait(LOCATORS['dm_loaded'],15)
            except WaitException:
                self.logger.error('chat didnt loaded in time... trying again')
                self.driver.get(f'https://www.instagram.com/direct')
                err = go_to_user_dm()
                if err:
                    return err
                try:
                    self.__wait(LOCATORS['dm_loaded'],15)
                except WaitException:
                    self.logger.error('chat didnt loaded 2 consecutive times')
                    return 'error'
                
        
        self.logger.debug(
            f"send_msg() called with parameters to_username: {to_username}, msg: {msg}")

        err = load_chat()
        if err:
            return err

        if skip_if_already_messaged and self.__is_element_present(LOCATORS['dm_already_sent']):
            return 'already sent'

        resp = self.__wait_for_first_element_or_url([
            LOCATORS["dm_msg_field"],
            LOCATORS["dm_not_everyone"],
            LOCATORS['dm_invite_sent'],
            ],10)
        
        if resp == 0:
            msg_field = self.__wait(LOCATORS["dm_msg_field"],0)
        elif resp == 1:
            return "not everyone"
        elif resp == 2:
            return 'invite already sent'
        elif resp == False: 
            self.logger.error(f'dm page is not loading or unexpected message not yet known. Please contact maintainer to fix that')
            return 'error'

        

        if self.dm_notification_disabled == False:
            self.__check_dm_notification()
            
        err = self.__paste_msg_in_dm(msg,msg_field)
        if err:
            return err 

        err = self.__check_is_sent()
        if err:
            return err
  
        return "sent" 

        

    def __check_dm_notification(self):
        if self.__is_element_present(LOCATORS["dm_notification_disable"], 4):
            self.__wait_and_click(LOCATORS["dm_notification_disable"], 2)
            self.dm_notification_disabled = True
        else:
            self.dm_notification_disabled = True


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
                    return "not everyone"
        except StaleElementReferenceException:
            self.logger.error("StaleElementReferenceException")
            return 'try again'
        

    @ensure_logged
    def go_to_url(self,url):
        self.driver.get(url)

    def _move_primary_general(self):
        self.__wait_and_click('//*[@aria-label="Conversation information"]',2)

        self.__wait_and_click('//div[@role="button" and text()="Move"]',5)
        sleep(1)

    def _get_current_messages(self,i=0):
        i+= 1
        if i == 5:
            raise BrokenChatException()
        
        def get_list(list_of_msg_webelements) -> list:
            msg = []
            for webelement in list_of_msg_webelements:
                msg.append(webelement.text)
            return msg
        try:
            assistant = self.__wait_for_all("//div[contains(@style,'background-color: rgb(55, 151, 240)')]",5)
        except:
            self.driver.refresh()
            return self._get_current_messages(i)
        

        assistant_msg = get_list(assistant)
        try:
            user = self.__wait_for_all("//div[contains(@style,'background-color: rgb(var(--ig-highlight-background))')]",5)
            user_msg = get_list(user)
        except:
            user_msg = []

        all = self.__wait_for_all('//div[@aria-label="Double tap to like"]',5)
        all_msg = get_list(all)

        self.logger.info(f'found {len(all_msg)} messages')
        self.logger.debug(f"{self.__get_id_from_url(self.driver.current_url),all_msg, user_msg, assistant_msg}")

        return self.__get_id_from_url(self.driver.current_url),all_msg, user_msg, assistant_msg

    @ensure_logged
    def get_new_context(self,first=True):

        if not "https://www.instagram.com/direct/" in self.driver.current_url:
            self.driver.get("https://www.instagram.com/direct/")
        sleep(1)
        
        if self.dm_notification_disabled == False:
            self.__check_dm_notification()

        try:
            new_msgs = self.__wait_for_all('//span[@data-visualcompletion="ignore"]/parent::div/parent::div/parent::div/parent::div')
        except:
            return "no new messages"
        
        #self.logger.info(new_msgs)
        
        new_msgs[0 if first else -1].location_once_scrolled_into_view
        new_msgs[0 if first else -1].click()
        sleep(3)

        return self._get_current_messages()
        
 