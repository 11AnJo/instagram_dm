import undetected_chromedriver as uc

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import time
import logging
import sys, os
from selenium.common.exceptions import StaleElementReferenceException



LOCATORS = {
            "cookie_accept":"//button[text()='Decline optional cookies']",
            "cookie_text":"//*[text()='Allow the use of cookies from Instagram on this browser?']",
            "login_username_field":"//input[@name='username']",
            "login_password_field":"//input[@name='password']",
            "new_dm_btn":"//div[@role= 'button'][.//div//*//*[text()='New message']]",
            "dm_type_username":"//input[@placeholder='Search...']",
            "dm_select_user":'//span/span/span[text()="{}"]',
            "dm_user_not_found":"//span[text()='No account found.']",
            "dm_start_chat_btn": "//div/div[text()='Chat' and @role='button']",
            "dm_msg_field":"//div[@role='textbox' and @aria-label='Message']",
            "dm_notification_present":"//span[text()='Turn on Notifications']",
            "dm_notification_disable":"//button[text()='Not Now']",
            "dm_send_button":"//div[@role='button' and text()='Send']",
            "dm_error_present":"//*[text()='IGD message send error icon']",
            "2f_screen_present":"//input[@aria-describedby='verificationCodeDescription' and @aria-label='Security Code']",
            "2f_entering_error":"//p[@id='twoFactorErrorAlert' and @role='alert']",
            "check_dm_message_sent_to_user":"//div[@role='none']//div[@dir='auto' and @role='none']",
            "login_error":"//p[@id='slfErrorAlert']"
        }

class WaitAndClickException(Exception):
    pass

class WaitException(Exception):
    pass

class User:
    def __init__(self,profile_name,debug=False,starting_page='https://www.instagram.com/direct/'):
        self.cookies_dict = None
        self.profile_name = profile_name
        self.debug = debug
        self.logger = self.__initialize_log()
        self.starting_page = starting_page

        self.driver = self.__init_driver()
        self.driver.get(self.starting_page)

        if not self.driver.current_url == self.starting_page:
            self.logger.info("account not logged in. Please login and click enter")
            input(":")

    

    def __initialize_log(self):
        logger = logging.getLogger(f"main")

        logger.setLevel(logging.DEBUG)

        if self.debug:
            stream_level = logging.DEBUG
        else:
            stream_level = logging.INFO

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(stream_level)

        newly_created = False
        if not os.path.isdir('./log'):
            newly_created = True
            os.makedirs('./log')

        file_handler = logging.FileHandler(f'log/{self.profile_name}.log')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        if newly_created:
            logger.debug("log folder was not found. Created new one")

        return logger


    def __init_driver(self):
        return uc.Chrome(user_data_dir=f"{os.getcwd()}/profiles/{self.profile_name}")
         
    
    def __wait_and_click(self, xpath,time=5):
        self.logger.debug(f'__wait_and_click() - called with xpath: {xpath}, time: {time}')
        try:
            button = WebDriverWait(self.driver, time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()
            self.logger.debug(f"Clicked the element with xpath: {xpath}")
        except Exception as e:
            self.logger.debug(f"Could not click the element with xpath: {xpath}. Error: {str(e)}")
            raise WaitAndClickException(f"Stopping execution due to failure to click on element: {xpath}") from e


    def __wait(self, xpath,time=5):
        self.logger.debug(f'__wait() - called with xpath: {xpath}, time: {time}')
        try:
            return WebDriverWait(self.driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception as e:
            self.logger.debug(f"Could not wait for the element with xpath: {xpath}. Error: {str(e)}")
            raise WaitException(f"Stopping execution due to failure in waiting for element: {xpath}") from e



    def get_suggestions(self,username):
        def get_all_usernames():
            usernames = set()
            repeated_count = 0
            threshold = 5  # Adjust the threshold as needed
            
            while True:
                elements = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a//div//span//div')))
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
                self.driver.execute_script("arguments[0].scrollIntoView();", elements[-1])
                time.sleep(1)  # Adjust the sleep time as needed
                
            return usernames




        LOCATORS_SUGGESTIONS = {
        'page_unavailable':"//span[text()='Sorry, this page isn't available.']",
        'suggest_button':"//div[@role='button']//div//*[local-name() = 'svg']",
        'see_all_button':"//a[@role='link']//span[@dir='auto' and text()='See all']",
        'similar_acc_presence':"//div[text()='Suggested for you']",
        'err_unable_to_load':"//div[text()='Unable to load suggestions.']"
        }

        try:

            self.logger.debug(f"get_suggestions() - called with username: {username}")

            self.driver.get(f'https://www.instagram.com/{username}')
            try:
                self.__wait_and_click(LOCATORS_SUGGESTIONS['suggest_button'])
            except WaitAndClickException:
                if self.__is_element_present(LOCATORS_SUGGESTIONS["page_unavailable"]):
                    self.logger.debug("Profile is unavailable")
                    return "Profile is unavailable"
                self.logger.exception("AJAJ")
                
            if self.__is_element_present(LOCATORS_SUGGESTIONS['err_unable_to_load'],3):
                return 'acc locked'

            self.__wait_and_click(LOCATORS_SUGGESTIONS['see_all_button'])
            
            self.__wait(LOCATORS_SUGGESTIONS['similar_acc_presence'])
            return get_all_usernames()

        except WaitAndClickException as e:
            self.logger.error(f"get_suggestions() - Stopping execution. Error: {str(e)}")
            return False
        except WaitException as e:
            self.logger.error(f"get_suggestions() - Stopping execution. Error: {str(e)}")
            return False



    def __exit_driver(self):
        self.driver.quit()

    def get_cookies(self,close_after=True):
        def transform_cookies(cookies):
            headers = {}
            cookie_str = ""
            for cookie in cookies:
                cookie_str += cookie['name'] + "=" + cookie['value'] + "; "
            headers["Cookie"] = cookie_str[:-2]  # remove the last semicolon and space
            headers["X-Ig-App-Id"]="936619743392459"        # <---------------------
            return headers
    
        try:
            
            cookies = self.driver.get_cookies()
            cookies_dict = transform_cookies(cookies)
            if close_after:
                self.__exit_driver()

            self.cookies_dict = cookies_dict
            return cookies_dict
        except:
            self.logger.exception("get_cookies")
    
    


    def __is_element_present(self, xpath, time_to_wait=0):

        wait = WebDriverWait(self.driver, time_to_wait)
        self.logger.debug(f"__is_element_present() called with parameters: xpath: {xpath} time to wait: {time_to_wait}")
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.logger.debug("__is_element_present() returning True")
            return True
        except:
            self.logger.debug("__is_element_present() returning False")
            return False
        


    def send_msg(self,to_username,msg,check_dm_message=False):
        def check_dm_message_sent_to_user():
            return self.__is_element_present(LOCATORS['check_dm_message_sent_to_user'],2)
        
        def check_if_freezed():
            return self.__is_element_present(LOCATORS["dm_error_present"],3)
                

        try:
            self.logger.debug(f"send_msg() called with parameters to_username: {to_username}, msg: {msg}")

            if not self.__is_element_present(LOCATORS["new_dm_btn"],0):
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
            action.send_keys(msg)
            action.perform()
            #send_btn = self.driver.find_element("xpath",LOCATORS["dm_send_button"])
            #send_btn.click()
            #msg_field.send_keys(Keys.ENTER)
            
            
            if check_if_freezed() == True:
                self.logger.warn("acc freezed")
                return "freeze"
            
            # If the action is successful, break the loop    
            return "sent"

                

        except:
            self.logger.exception("send_msg()")
            return "error"

        
        
        
        
    
        
        
