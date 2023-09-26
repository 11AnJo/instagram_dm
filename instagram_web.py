from selenium import webdriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import time
import logging
import sys
import os
from selenium.common.exceptions import StaleElementReferenceException
import pyotp
import re

LOCATORS = {
    "cookie_accept": "//button[text()='Decline optional cookies']",
    "cookie_text": "//*[text()='Allow the use of cookies from Instagram on this browser?']",
    "login_username_field": "//input[@name='username']",
    "login_password_field": "//input[@name='password']",
    "new_dm_btn": "//div[@role= 'button'][.//div//*//*[text()='New message']]",
    "dm_type_username": "//input[@placeholder='Search...']",
    "dm_select_user": '//span/span/span[text()="{}"]',
    "dm_user_not_found": "//span[text()='No account found.']",
    "dm_start_chat_btn": "//div/div[text()='Chat' and @role='button']",
    "dm_msg_field": "//div[@role='textbox' and @aria-label='Message']",
    "dm_notification_present": "//span[text()='Turn on Notifications']",
    "dm_notification_disable": "//button[text()='Not Now']",
    "dm_send_button": "//div[@role='button' and text()='Send']",
    "dm_error_present": "//*[text()='IGD message send error icon']",
    "2f_screen_present": "//input[@aria-describedby='verificationCodeDescription' and @aria-label='Security Code']",
    "2f_entering_error": "//p[@id='twoFactorErrorAlert' and @role='alert']",
    "check_dm_message_sent_to_user": "//div[@role='none']//div[@dir='auto' and @role='none']",
    "login_error": "//p[@id='slfErrorAlert']",
    "save_login_info": "//button[text()='Save Info']"
}


class WaitAndClickException(Exception):
    pass


class WaitException(Exception):
    pass


class BrokenChatException(Exception):
    pass

class User:
    def __init__(self, profile_name=None, username=None, password=None, token=None, debug=False, starting_page='https://www.instagram.com/direct/'):
        self.cookies_dict = None
        self.profile_name = profile_name
        self.username = username
        self.password = password
        self.token = token
        self.starting_page = starting_page
        self.is_logged = False

        self.debug = debug
        self.logger = self.__initialize_log()

        self.driver = None

    def __initialize_log(self):
        logger = logging.getLogger(
            f"instagram_web - {self.profile_name if self.profile_name else self.username}")
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        newly_created = False
        if os.path.isdir('./log'):
            pass
        else:
            newly_created = True
            os.makedirs('./log')
        file_handler = logging.FileHandler(
            f'log/{self.profile_name if self.profile_name else self.username}.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        if newly_created:
            logger.debug("log folder was not found. Created new one")
        return logger

    def __make_sure_its_logged(self):
        if self.driver == None:
            self.logger.info("driver not active")
            self.driver = self.__init_driver()

        if not self.is_logged:
            self.logger.info("login not active")
            self.login()

    def __init_driver(self):
        options = uc.ChromeOptions()
        if self.profile_name:
            data_dir = f"{os.getcwd()}/profiles/{self.profile_name}"
            # e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
            options.add_argument(f"--user-data-dir={data_dir}")
        # options.add_argument(r'--profile-directory=YourProfileDir') #e.g. Profile 3
        options.add_argument("--lang=en_US")
        self.driver = uc.Chrome(options=options)

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
                f"Could not wait for the element with xpath: {xpath}. Error: {str(e)}")
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

    def get_suggestions(self, username):
        self.__make_sure_its_logged()

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

    def get_cookies(self, close_after=True):
        self.__make_sure_its_logged()

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

    def __accept_cookie(self):
        self.logger.debug(f"__accept_cookie() called")
        try:
            self.__wait_and_click(LOCATORS["cookie_accept"], 2)
        except WaitAndClickException:
            self.logger.info("No cookies to accept")

    def __two_factor(self):
        url = self.driver.current_url
        self.logger.debug("looking for 2f")
        try:
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
            self.driver = self.__init_driver()

        self.driver.get('https://www.instagram.com/direct/')
        if self.driver.current_url == 'https://www.instagram.com/direct/':
            self.is_logged = True
            return True

        if self.username == None and self.password == None:
            self.driver.get('https://instagram.com/accounts/login')

            self.logger.info(
                "Username and password not specified. Please login by yourself")
            while True:
                sleep(0.5)
                if "instagram.com/accounts/onetap" in self.driver.current_url:
                    self.__wait_and_click(LOCATORS["save_login_info"])

                    self.driver.get("https://www.instagram.com/direct/inbox")

                    try:
                        self.__wait_and_click(
                            LOCATORS["dm_notification_disable"], 3)
                    except WaitAndClickException:
                        self.logger.info("No dm notification")
                    self.logger.info(f"Login succesfull to")
                    self.is_logged = True
                    return True

        try:
            self.driver.get('https://instagram.com/accounts/login')

            self.__accept_cookie()
            self.__wait(LOCATORS["login_username_field"],
                        1).send_keys(self.username)
            a = self.__wait(LOCATORS["login_password_field"], 1)
            a.send_keys(self.password)
            a.send_keys(Keys.ENTER)

            # self.__paste_text(LOCATORS["login_username_field"],self.username,1)
            # self.__paste_text(LOCATORS["login_password_field"],self.password)

            if self.__is_element_present(LOCATORS['login_error'], 2):
                self.logger.error(
                    f"There was a problem logging you into Instagram. Please try again soon.")
                return "There was a problem logging you into Instagram. Please try again soon."

            if self.token:
                self.logger.debug("two factor is on, trying to login")
                self.__two_factor()

            self.__wait_and_click(LOCATORS["save_login_info"],10)
            sleep(2)

            self.driver.get("https://www.instagram.com/direct/inbox")

            try:
                self.__wait_and_click(LOCATORS["dm_notification_disable"], 3)
            except WaitAndClickException:
                self.logger.info("No dm notification")
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

    def send_msg_to_id(self,msg_id,msg):
        if msg_id not in self.driver.current_url:
            self.driver.get(f'https://www.instagram.com/direct/t/{msg_id}')

        msg_field = self.__wait(LOCATORS["dm_msg_field"])

        action = ActionChains(self.driver)
        action.move_to_element(msg_field)
        action.click()
        action.send_keys(msg+"\n")
        action.perform()  
        

        #dm_id = self.__get_id_from_url(self.driver.current_url)
        return "sent" 

    def send_msg(self, to_username, msg, check_dm_message=False):
        self.__make_sure_its_logged()

        def check_dm_message_sent_to_user():
            return self.__is_element_present(LOCATORS['check_dm_message_sent_to_user'], 2)

        def check_if_freezed():
            return self.__is_element_present(LOCATORS["dm_error_present"], 3)

        try:
            self.logger.debug(
                f"send_msg() called with parameters to_username: {to_username}, msg: {msg}")

            if not self.__is_element_present(LOCATORS["new_dm_btn"], 0):
                self.driver.get("https://www.instagram.com/direct/")

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

            msg_field = self.__wait(LOCATORS["dm_msg_field"])

            if check_dm_message:
                if check_dm_message_sent_to_user():
                    return 'already sent'

            action = ActionChains(self.driver)
            action.move_to_element(msg_field)
            action.click()
            action.send_keys(msg+"\n")
            action.perform()
            # send_btn = self.driver.find_element("xpath",LOCATORS["dm_send_button"])
            # send_btn.click()
            # msg_field.send_keys(Keys.ENTER)

            if check_if_freezed() == True:
                self.logger.warn("acc freezed")
                return "freeze"

            
            dm_id = self.__get_id_from_url(self.driver.current_url)
            self.logger.info(dm_id)

            return "sent"

        except:
            self.logger.exception("send_msg()")
            return "error"

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

    def get_new_context(self,first=True):
        self.__make_sure_its_logged()

        if not "https://www.instagram.com/direct/" in self.driver.current_url:
            self.driver.get("https://www.instagram.com/direct/")
        sleep(1)

        try:
            new_msgs = self.__wait_for_all('//span[@data-visualcompletion="ignore"]/parent::div/parent::div/parent::div/parent::div')
        except:
            return "no new messages"
        
        #self.logger.info(new_msgs)
        
        new_msgs[0 if first else -1].location_once_scrolled_into_view
        new_msgs[0 if first else -1].click()
        sleep(3)

        return self._get_current_messages()
        
