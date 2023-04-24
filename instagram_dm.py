from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
import time
import logging
import sys
import pyotp

from firefox_setup import initialize_driver


LOCATORS = {
            "cookie_accept":"//button[text()='Only allow essential cookies']",
            "cookie_text":"//*[text()='Allow the use of cookies from Instagram on this browser?']",
            "login_username_field":"//input[@name='username']",
            "login_password_field":"//input[@name='password']",
            "dm_select_user":'//span[text()="{}"]',
            "dm_select_user_btn": "//button/div[text()='Next']",
            "dm_msg_field":"//textarea[@placeholder='Message...']",
            "dm_notification_present":"//span[text()='Turn on Notifications']",
            "dm_notification_disable":"//button[text()='Not Now']",
            "dm_send_button":"//div[@role='button' and text()='Send']",
            "dm_error_present":"//p[text()='Something went wrong. Please try again.']",
            "2f_screen_present":"//input[@aria-describedby='verificationCodeDescription' and @aria-label='Security Code']",
            "2f_entering_error":"//p[@id='twoFactorErrorAlert' and @role='alert']"
        }





    


class User:
    def __init__(self,username,password,token=False,debug=False, use_chrome=False):
        self.username = username
        self.password = password
        self.two_factor_token = token

        self.cookies_dict = None

        self.is_logged = False

        self.debug = debug
        self.logger = self.__initialize_log()


        self.driver = None
        self.wait = None
        self.use_chrome = use_chrome
        

    def __initialize_log(self):
        logger = logging.getLogger(f"instagram_web acc - {self.username}")
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(f'log/acc-{self.username}.log')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        return logger


    def __initialize_driver(self, use_chrome=False):
        try:
            self.logger.debug('initialize_driver() called with debug=%s', self.debug)
            if use_chrome:
                self.driver, self.wait = initialize_chrome_driver()
            else:
                self.driver, self.wait = initialize_driver()
            self.__accept_cookie(self.driver)
            self.logger.debug("driver initialized")
        except:
            self.logger.exception("__initialize_driver")


    def __generate_2factor_code(self,token):
        totp = pyotp.TOTP(token)
        current_time = time.time()
        time_step = 30  # TOTP time step, usually 30 seconds
        remaining_time = time_step - (current_time % time_step)

        # If the code is valid for less than 5 seconds, wait for the next one
        if remaining_time < 4:
            time.sleep(remaining_time)

        new_code = totp.now()
        return new_code


    def __accept_cookie(self,driver):
        self.logger.debug(f"__accept_cookie() called with parameters: driver={driver}" )
        try:
            driver.get('https://instagram.com/')
            if self.wait.until(EC.presence_of_element_located((By.XPATH, LOCATORS["cookie_text"]))):
                driver.find_element("xpath",LOCATORS["cookie_accept"]).click()
                self.logger.debug("cookie accepted")
                sleep(2)
            else:
                self.logger.warning("No cookies to accept!")
        except:
            self.logger.exception("__accept_cookie")
    

    def __two_factor(self):
        try:
            url = self.driver.current_url
            self.logger.debug("in 5 sec looking for 2f presence")
            sleep(5)
            two_factor_token_field = self.wait.until(EC.presence_of_element_located((By.XPATH, LOCATORS['2f_screen_present'])))
            two_factor_token_field.send_keys(self.__generate_2factor_code(self.two_factor_token))
            two_factor_token_field.send_keys(Keys.RETURN)
            
            if self.__is_element_present(LOCATORS['2f_entering_error'],3):
                self.logger.error("2f_entering_error")
                sleep(5)
                two_factor_token_field.send_keys(Keys.CONTROL,"a") # delete old
                two_factor_token_field.send_keys(Keys.DELETE)
                two_factor_token_field.send_keys(self.__generate_2factor_code(self.two_factor_token))
                two_factor_token_field.send_keys(Keys.RETURN)
                if self.__is_element_present(LOCATORS['2f_entering_error'],3):
                    self.logger.error("second 2f_entering_error, cannot login")
                    return "cannot login"
                
            for i in range(10):
                if self.driver.current_url != url:
                    return True
                self.logger.debug("after entering code and 5s no change in url")
                sleep(1)
            return "cannot login"
        except:
            self.logger.exception("two_factor()")
            return "cannot login"


    def login(self):
        self.__initialize_driver(use_chrome=self.use_chrome)
        self.logger.debug(f"login() called for {self.username}:{self.password}")
        try:
            self.driver.get('https://instagram.com/login')
            username_field = self.wait.until(EC.presence_of_element_located((By.XPATH, LOCATORS["login_username_field"])))
            password_field = self.driver.find_element("xpath",LOCATORS["login_password_field"])
            url = self.driver.current_url
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)
            
            if self.__is_element_present("//p[@id='slfErrorAlert']",5):
                self.logger.error(f"There was a problem logging you into Instagram. Please try again soon.")
                return "There was a problem logging you into Instagram. Please try again soon."


            #wait for instagram to login
            while True:
                if self.driver.current_url != url:
                    self.logger.debug(f"two factor token: {self.two_factor_token}")
                    if self.two_factor_token:
                        self.logger.debug("two factor is on, trying to login")
                        self.__two_factor()



                    self.driver.get("https://www.instagram.com/direct/inbox")
                    
                    self.wait.until(EC.presence_of_element_located((By.XPATH,LOCATORS["dm_notification_present"])))
                    notifications = self.driver.find_element("xpath",LOCATORS["dm_notification_disable"])
                    notifications.click()
    
                    self.logger.info(f"Login succesfull to")
                    self.is_logged = True
                    return True
                sleep(1)
    
        except:
            self.logger.exception("login")


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
            
            self.login()
            cookies = self.driver.get_cookies()
            cookies_dict = transform_cookies(cookies)
            if close_after:
                self.__exit_driver()

            self.cookies_dict = cookies_dict
            return cookies_dict
        except:
            self.logger.exception("get_cookies")
    
    


    def __is_element_present(self, xpath, time_to_wait):

        wait = WebDriverWait(self.driver, time_to_wait)
        self.logger.debug(f"__is_element_present() called with parameters: xpath: {xpath} time to wait: {time_to_wait}")
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.logger.debug("__is_element_present() returning True")
            return True
        except:
            self.logger.debug("__is_element_present() returning False")
            return False
        


    def send_msg(self,to_username,msg):
        def select_user(elements):
            if elements and len(elements) > 0:
                elements[0].click()    
            next_btn = wait.until(EC.presence_of_element_located((By.XPATH, LOCATORS["dm_select_user_btn"])))
            self.driver.execute_script("arguments[0].click();", next_btn)
        

        try:
            self.logger.debug(f"send_msg() called with parameters to_username: {to_username}, msg: {msg}")

            if not self.is_logged:
                self.logger.debug("acc not logged in. Trying to login")
                self.login()


            wait = WebDriverWait(self.driver, 10)
            self.driver.get("https://www.instagram.com/direct/new/?hl=en")
            
            search_user_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='queryBox']"))) #new dm button
            search_user_field.send_keys(to_username)
            elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, LOCATORS["dm_select_user"].format(to_username))))  #wait for instagram to show list

            if self.__is_element_present("//div[text()='No account found.']",0):
                self.logger.info(f"Account not found: {to_username}")
                return "Account not found"
            
            select_user(elements)#from list
            #

            wait_2 = WebDriverWait(self.driver, 5)
            try:
                # Look for the "Something went wrong" message
                error_messages = wait_2.until(EC.presence_of_all_elements_located((By.XPATH,LOCATORS["dm_error_present"])))
                for message in error_messages:
                    if message.text == "Something went wrong. Please try again.":
                        self.logger.debug("acc freezed")

                        return "freeze" 
            except:
                msg_field = wait.until(EC.presence_of_element_located((By.XPATH,LOCATORS["dm_msg_field"])))
                msg_field.send_keys(msg)
                send_btn = self.driver.find_element("xpath",LOCATORS["dm_send_button"])
                send_btn.click()
                #TODO check if message popped up
                return "sent"  
            
        except:
            self.logger.exception("send_msg()")
            return 'error'
        
        
        
    
        
        