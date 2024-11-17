import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from get_credentials import get_credentials
from selenium_docker_ctrl import selenium_docker_ctrl, check_docker_installed
from utils import format_elapsed_seconds, setup_logger, parse_creation_date, format_elapsed_seconds
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from typing import List

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
        self.homeurl = None
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


    def check_login_athome(self):
        # Wait for either login success (URL contains 'mailbox/inbox') or login failure (login_error element)
        print("check for login status at homepage")
        WebDriverWait(self.driver, 60).until(
            lambda d: ("mailbox/inbox" in d.current_url) or 
                    EC.visibility_of_element_located((By.ID, "login_error"))(d)
        )
        
        # Check if login was successful by URL
        if "mailbox/inbox" in self.driver.current_url:
            print("Login successful! Now at homepage. ")
            self.logged_in = True
            self.homeurl = self.driver.current_url
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
        
        max_attempts=attempts
        while attempts > 0:
            if max_attempts>1:
                print(f'attempt {max_attempts-attempts+1}, max attempts {max_attempts}')
            try:
                login()
                # Make sure we are logged in at home
                self.check_login_athome()
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
        except Exception as e:
            raise RuntimeError(f"Failed to verify Sent Mail page status: {e}")

    def navigate_sentmail(self):
        sentmail_url = self.homeurl.replace("inbox", "sent")
        self.driver.get(sentmail_url)

        # # Click on the sentmail_button
        # leftside_bar = WebDriverWait(self.driver, 60).until( \
        #     EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/aside[1]')))
        # mailbox_button = WebDriverWait(leftside_bar, 60).until( \
        #     EC.presence_of_element_located((By.XPATH, './/section/ul/li[1]/a')))
        # mailbox_button.click()

        # sentmail_button = WebDriverWait(leftside_bar, 60).until(
        #     EC.element_to_be_clickable((By.XPATH, ".//section/ul/li[1]/ul/li[4]/a"))
        # )
        # sentmail_button.click()
        
    
    def __getSentmailrows(self):
        # need to make sure is in sentmail page.
        self.check_sentmailpage_status()
        # Locate the <tbody> tag where the table is at, and get all the rows. 
        table = WebDriverWait(self.driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/aside[2]//section[@class='content']//table"))
        )
        tbody = WebDriverWait(table, 60).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
        )    
        rows = WebDriverWait(tbody, 60).until(
            EC.visibility_of_all_elements_located((By.TAG_NAME, 'tr'))
        )
        return rows

    def get_shipnotice_idxs(self, app_env:str) -> List[int]:
        """
        # Inside sent mails, find the rows where Subject="Accepted -Ship Notice....."
        # If dev, use env var: daterange=> datetime.now().date()~os.environ["DEV_CRAWL_UNTIL"]
        # Else, let user type the date range. 
        """
        crawluntil=None
        if app_env=="prod":
            # let user type in the crawuntil date
            pass
        else: # dev, test
            crawluntil = datetime.fromisoformat(os.environ["DEV_CRAWL_UNTIL"])
        # Set date format of 'creation_date' in iExchangeWeb
        date_format = "%m/%d/%Y %I:%M %p"
        
        rows = self.__getSentmailrows()
        ship_notice_idxs=[]
        for i, row in enumerate(rows):
            # get creationdate string and parse it to date object for comparison
            creation_date_str = WebDriverWait(row, 60).until( \
                EC.presence_of_element_located((By.XPATH, "./td[11]"))).text
            creation_date = parse_creation_date(creation_date_str, date_format)
            # stop including the idx if creation_date earlier than crawluntil
            if creation_date < crawluntil: 
                logger.info(f'early stop at creation_date: {creation_date}')
                break            
            # get the text that indicates shipnotice or not (column "subject") 
            subject_str = WebDriverWait(row, 60).until( \
                EC.presence_of_element_located((By.XPATH, "./td[10]"))).text
            # find the rows that indicates its a ship notice
            if subject_str.startswith('Accepted -Ship Notice'):
                ship_notice_idxs.append(i)
            else: continue
        return ship_notice_idxs
        
    def crawl_shipnotices(self, shipnotice_idxs:List[int], app_env:str) -> pd.DataFrame:
        def check_EDIpage_status():
            # Make sure that the navigated EDI item page is normal. 
            # checks url and section element's presence
            assert WebDriverWait(self.driver, 60).until(
                    EC.url_contains('mailbox/item')
            ), "url doesnt contain 'mailbox/item'"
            assert WebDriverWait(self.driver, 60).until( \
                EC.visibility_of_all_elements_located((By.XPATH, "/html/body/div[2]/aside[2]/section"))
            ), "section XPATH not all elements are not visible"
        
        def switch_to_iframe():
            # Need to Switch to iFrame first, because all the data (#document) is in under an iframe! 
            # Find the iframe element by id
            iframe_locator = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.ID, 'contentFrame'))
            )
            assert iframe_locator is not None, "iframe with ID 'contentFrame' not found"
            
            # Switch to the iframe context
            WebDriverWait(self.driver, 60).until(
                # If the frame is available it switches the given driver to the specified frame.
                EC.frame_to_be_available_and_switch_to_it(iframe_locator)
            )

        def get_tables_from_iframe():
            # driver now represents iframe
            ship_notice_body = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '/html/body'))
            )
            
            # get all tables
            tables = WebDriverWait(ship_notice_body, 60).until(
                EC.presence_of_all_elements_located((By.XPATH, './table'))
            )
            assert tables is not None, "tables in ship_notice_body are not found!"
            return tables

        def crawl_tables_to_df(tables, df_shipNotice):
            sharedAttr_dict = dict()
            for j, table in enumerate(tables):
                if j==0:
                    ship_notice_title = WebDriverWait(table, 60).until(
                        EC.presence_of_element_located((By.XPATH, './tbody/tr[1]/td/h1'))
                    ).text
                else:
                    upperleftmost_element = WebDriverWait(table, 60).until(
                        EC.presence_of_element_located((By.XPATH, "./tbody/tr/td[1]/table/tbody/tr[1]"))
                    )
                    upperleftmost_caption_element = WebDriverWait(upperleftmost_element, 60).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "caption"))
                    )
                    upperlefmost_caption = upperleftmost_caption_element.text.strip()
                    if upperlefmost_caption == "Ship To":
                        data_element = WebDriverWait(upperleftmost_caption_element, 60).until(
                            EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                        )
                        sharedAttr_dict['ship_to'] = data_element.text
                    elif upperlefmost_caption == "Ship Notice #":
                        # get all elements with "caption" classes in the table.tbody element (table.tbody)
                        all_caption_elements = WebDriverWait(table, 60).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "caption"))
                        )
                        for count, caption_element in enumerate(all_caption_elements):
                            if caption_element.text.strip() == 'Ship Notice #':
                                # find sibling (data)
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                sharedAttr_dict['ship_notice_num'] = data_element.text
                            elif caption_element.text.strip() == 'Create Date/Time':
                                # find sibling (data)
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                sharedAttr_dict['create_datetime'] = data_element.text
                            elif count>=2: break
                    elif "Order #" in upperlefmost_caption or "PO #" in upperlefmost_caption: # items
                        itemAttr_dict = {}
                        all_caption_elements = WebDriverWait(table, 60).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "caption"))
                        )
                        for count, caption_element in enumerate(all_caption_elements):
                            caption = caption_element.text
                            if "Order #" in caption or "PO #" in caption:
                                # find sibling (data)                                
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                if 'Order #' in caption:
                                    # itemAttr_dict['order_type'] = 'Buyer'
                                    itemAttr_dict['order_num'] = data_element.text
                                else: # PO num
                                    # itemAttr_dict['order_type'] = 'Purchase'
                                    itemAttr_dict['order_num'] = data_element.text[:6] # first 6 digits
                            elif 'Buyer Part #' in caption: 
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                itemAttr_dict['buyer_part_num'] = data_element.text
                            elif 'Ship Quantity' in caption: 
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                itemAttr_dict['ship_quantity'] = data_element.text
                            elif count>=3:
                                break
                        
                        # combine a attributes for a single item at a column level
                        df_row = pd.DataFrame.from_dict([{**sharedAttr_dict, **itemAttr_dict}])
                        # concat items to a allItems ship notice list at a row level
                        df_shipNotice = pd.concat([df_shipNotice, df_row], ignore_index=True)
                    else: continue
            return df_shipNotice

        df_shipNotice = pd.DataFrame()
        # To avoid stale element exception, find all rows every iteration. Think of a better way later
        sentmail_url = self.homeurl.replace("inbox", "sent")
        for idx in reversed(shipnotice_idxs): # reversed, start processing from earliest non-crawled date.
            # Access EDI page using the view button in a single row. 
            # To avoid stale element exception, go back to sentmail page and find all rows everytime.
            self.driver.get(sentmail_url)
            row = self.__getSentmailrows()[idx]            
            try:
                # Access through relative XPATH
                view_button = WebDriverWait(row, 60).until(
                    EC.element_to_be_clickable((By.XPATH, './td[14]/button[1]'))
                )
                view_button.click()
            except ElementClickInterceptedException:
                # Click using JavaScript as a fallback. Occassionally there's an element blocking the button. 
                logger.info(f'Click using JavaScript as a fallback at idx={idx}')
                self.driver.execute_script("arguments[0].click();", view_button)
            check_EDIpage_status()
            print(f'navigated to edi page! idx={idx}')

            # Before getting the desired data, need to switch to iframe first
            switch_to_iframe()

            # Get the desired data
            tables = get_tables_from_iframe()
            df_shipNotice = crawl_tables_to_df(tables, df_shipNotice)
            print(f"finish idx {idx}! At total runtime at: {time.time()-self.script_run_time}")
        print(f"finish processing! ")
        return df_shipNotice

            









