import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from get_credentials import get_credentials
from selenium_docker_ctrl import selenium_docker_ctrl, check_docker_installed
from utils import format_elapsed_seconds, setup_logger
from dotenv import load_dotenv

timeout = 60
logger = setup_logger()
load_dotenv()

class MyLoginError(Exception):
    """Exception raised for errors in the login process."""
    def __init__(self, message="Login failed. Username or Password incorrect. \nTry again. (Hit Ctrl-C to Exit)"):
        self.message = message
        super().__init__(self.message)


class SeleniumHelper:
    def __init__(self, script_start_time):
        self.driver = None
        self.logged_in = False
        self.script_run_time = script_start_time
    
    @staticmethod
    def is_selenium_server_up(url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            return False
        return False

    @staticmethod
    def wait_until_selenium_server_up(selenium_url, timeout = timeout):
        # Wait for the Selenium server to be ready
        # timeout=Total wait time (seconds)
        poll_interval = 2  # Time between polls (seconds)
        start_time = time.time()

        while time.time() - start_time < timeout:
            if SeleniumHelper.is_selenium_server_up(selenium_url):
                print("Selenium server is up and running.")
                break
            print("Waiting for Selenium server to start...")
            time.sleep(poll_interval)
        else:
            raise RuntimeError("Selenium server did not start within the timeout period.")

    @staticmethod
    def setup_selenium_env():
        # Setup Selenium Docker Environment
        check_docker_installed()        
        selenium_url = 'http://localhost:7900/?autoconnect=1&resize=scale&password=secret'
        # Stop container first if previous execution failed to stop selenium docker. 
        if SeleniumHelper.is_selenium_server_up(selenium_url):   
            selenium_docker_ctrl('stop')        
        selenium_docker_ctrl('start')
        SeleniumHelper.wait_until_selenium_server_up(selenium_url, timeout=60)

    def init_webdriver(self, timeout=timeout):
        # giving the path of chromedriver to selenium webdriver
        # Set up Chrome options
        poll_interval = 2  # Time between polls (seconds)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--disable-features=SidePanelPinning")
                self.driver = webdriver.Remote(
                    command_executor='http://localhost:4444/wd/hub',
                    options=chrome_options
                )
                return
            except:
                print(f'Driver not yet initialized, please WAIT until timeout={timeout} seconds.')
                time.sleep(poll_interval)
        else:
            raise RuntimeError("Selenium server did not start within the timeout period.")

    def quit_scraper(self):
        if self.driver:
            self.driver.quit()
        selenium_docker_ctrl('stop')
        elapsed_seconds = time.time() - self.script_run_time
        print(f'script run time = {format_elapsed_seconds(elapsed_seconds)}')
        input("\nPress Enter to exit...")
        print("Have a Nice Day!  (Exiting...)")
        exit(1)


    def check_login_status(self):
        # Wait for either login success (URL contains 'mailbox/inbox') or login failure (login_error element)
        print("check for login status")
        WebDriverWait(self.driver, 60).until(
            lambda d: ("mailbox/inbox" in d.current_url) or 
                    EC.visibility_of_element_located((By.ID, "login_error"))(d)
        )
        
        # Check if login was successful by URL
        if "mailbox/inbox" in self.driver.current_url:
            print("Login successful!")
            return
        elif EC.visibility_of_element_located((By.ID, "login_error"))(self.driver):
            raise MyLoginError
        else:
            raise Exception("Unexpected Login Error: Login Failed but Login Error Element not present.")

    def login_iExWeb(self, url, app_env, attempts=3):
        def login():
            # opening the website in chrome.
            # print('Opening iExchangeWeb URL....')
            self.driver.get(url)

            assert "iExchangeWeb" in self.driver.title, "not iExchangeWeb"
            if app_env=="prod":
                username, password = get_credentials()
            else: # dev, test
                username, password = os.environ["DEV_USERNAME"], os.environ["DEV_PASSWORD"]
            
            loginBox = WebDriverWait(self.driver, timeout).until( \
                EC.presence_of_element_located((By.ID, "login-box")))
            
            # find username input box
            userNameForm = WebDriverWait(loginBox, timeout).until( \
                EC.presence_of_element_located((By.ID, "userName")))
            userNameForm.send_keys(username)
            
            # find password input box
            passwordForm = WebDriverWait(loginBox, timeout).until( \
                EC.presence_of_element_located((By.ID, "password")))
            passwordForm.send_keys(password)
            # find submit button
            signin_button = WebDriverWait(loginBox, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#login-box .btn-primary"))
            )
            assert signin_button.text == 'Sign In', "error at: assert signin_button.text == Sign in"
            # click the submit button
            signin_button.click()
            self.check_login_status()
        
        max_attempts=attempts
        while attempts > 0:
            if max_attempts>1:
                print(f'attempt {max_attempts-attempts+1}, max attempts {max_attempts}')
            try:
                login()
                return
            except MyLoginError as e:
                attempts -= 1
                if attempts>0:
                    logger.error(f'MyLoginError. Retry. {e}')
                    print('\nRetry.')
            except Exception as e:
                attempts -= 1
                if attempts>0:    
                    print('\nUnexpected Error. Retry.')
                    logger.error(f'Unexpected Error. Retry. {e}')
        
        print("Exceeded max attempts.")        
    
    def check_sentmailpage_status(self):
        try:
            # Check if the URL contains 'mailbox/sent'
            WebDriverWait(self.driver, 60).until(
                EC.url_contains('mailbox/sent')
            )
            logger.info('Successfully navigated to the Sent Mail page!')

            # Check if the "Sent" text appears in the upper bar
            WebDriverWait(self.driver, 60).until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, "/html/body/div[2]/aside[2]/ol/li[2]"), "Sent"
                )
            )
            logger.info('"Sent" text is visible in the upper bar.')
            print("Navigated to sentmail page!")

        except Exception as e:
            raise RuntimeError(f"Failed to verify Sent Mail page status: {e}")

    def navigate_sentmail(self):
        # Click on the sentmail_button
        leftside_bar = WebDriverWait(self.driver, 60).until( \
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/aside[1]')))
        mailbox_button = WebDriverWait(leftside_bar, 60).until( \
            EC.presence_of_element_located((By.XPATH, './/section/ul/li[1]/a')))
        mailbox_button.click()

        sentmail_button = WebDriverWait(leftside_bar, 60).until(
            EC.element_to_be_clickable((By.XPATH, ".//section/ul/li[1]/ul/li[4]/a"))
        )
        sentmail_button.click()
        self.check_sentmailpage_status()
        
        





