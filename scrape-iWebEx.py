print('Welcome to the iExchangeWeb Scraper! \n\
      Ready to scrape some data? Let me sprinkle some magic. Just a moment...')
import sys, os, subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, WebDriverException
from selenium_docker_ctrl import selenium_docker_ctrl
from get_credentials import get_credentials

from datetime import datetime, timedelta
import pandas as pd
import time
import requests
import maskpass

script_run_time = time.time()

class MyLoginError(Exception):
    """Exception raised for errors in the login process."""
    def __init__(self, message="Login failed"):
        self.message = message
        super().__init__(self.message)

class MyShipNoticeCrawlingError(Exception):
    """Exception raised for errors in the single ShipNotice crawling process."""
    def __init__(self, message="ShipNotice crawling error. "):
        self.message = message
        super().__init__(self.message)


def check_docker_installed():
    try:
        x = subprocess.check_output('docker --version', stderr=subprocess.STDOUT)
        print(f"Great! I see you've already installed {x.decode('utf-8')}") # Print the Docker version if installed
    except FileNotFoundError as e:
        print(e)
        print('\nDocker is not installed. Please install Docker at https://docs.docker.com/get-docker/')
        raise

def is_selenium_server_up(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False
    return False

def wait_until_selenium_server_up(selenium_url, timeout = 60):
    # Wait for the Selenium server to be ready
    # timeout=Total wait time (seconds)
    poll_interval = 2  # Time between polls (seconds)
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_selenium_server_up(selenium_url):
            print("Selenium server is up and running.")
            break
        print("Waiting for Selenium server to start...")
        time.sleep(poll_interval)
    else:
        raise RuntimeError("Selenium server did not start within the timeout period.")

def init_webdriver(timeout=60):
    # giving the path of chromedriver to selenium webdriver
    # Set up Chrome options
    poll_interval = 2  # Time between polls (seconds)
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--disable-features=SidePanelPinning")
            driver = webdriver.Remote(
                command_executor='http://localhost:4444/wd/hub',
                options=chrome_options
            )
            return driver
        except:
            print(f'Driver not yet initialized, please WAIT until timeout={timeout} seconds.')
            time.sleep(poll_interval)
    else:
        raise RuntimeError("Selenium server did not start within the timeout period.")

def get_last_crawled_datetime(shipnotice_filepath: str) -> datetime:
    if not os.path.exists(shipnotice_filepath):
        print(f'First timer I suppose? No Problem! \n')
        input_date_format = "%m/%d/%Y"
        while True:
            input_date = input('Please enter the earliest date you want to crawl/scrape (MM/DD/YYYY): ')
            try:
                last_crawled_datetime = datetime.strptime(input_date, input_date_format)
                break
            except ValueError as e:
                print('Not a valid date, please give a date that matches the format MM/DD/YYYY')
        print(f'last_crawled_datetime set to: {last_crawled_datetime}')
    else:
        # last_crawled_datetime = newest date in database(ship-notice-total.csv)
        df_shipNotice_total = pd.read_csv(shipnotice_filepath)
        last_crawled_datetime = pd.to_datetime(df_shipNotice_total['create_datetime']).max()
        print(f'found {shipnotice_filename}, \n\
              last crawled date set to: {last_crawled_datetime}')    
    return last_crawled_datetime

def parse_creation_date(datetime_str: str, date_format) -> datetime:
    # 6/28/24 11:34 AM => 6/28/2024 11:34 AM
    date_part, time_part, meridiem = datetime_str.split(' ')
    month, day, year = date_part.split('/')
    full_year = f"20{year}"
    new_datetime_str = f"{month}/{day}/{full_year} {time_part} {meridiem}"
    creation_date = datetime.strptime(new_datetime_str, date_format)
    return creation_date

def format_elapsed_seconds(elapsed_seconds):
    # Convert elapsed time to timedelta
    elapsed_time = timedelta(seconds=elapsed_seconds)

    # Format the output using strftime
    formatted_time = str(elapsed_time).split()  # split into days, hours, minutes, seconds

    # Output the formatted time
    if len(formatted_time)>1:
        timetime = formatted_time[2].split(':')
        return f'Runtime: {formatted_time[0]}-days, {timetime[0]}-hrs, {timetime[1]}-mins, {round(float(timetime[2]), 2)}-secs'
    else: 
        timetime = formatted_time[0].split(':')
        return f'0-days, {timetime[0]}-hrs, {timetime[1]}-mins, {round(float(timetime[2]), 2)}-secs'

def save_to_shipnotice_daily(shipnoticefolder_path, df_shipNotice, idx_label = 'id'):
    fname_daily = f'ship-notice-{datetime.today().date()}_{datetime.today().hour}_{datetime.today().minute}.csv'
    filename_daily = os.path.join(shipnoticefolder_path, fname_daily)
    if len(df_shipNotice)>0:
        df_shipNotice.to_csv(filename_daily, index_label=idx_label)

def save_to_shipnotice_total(shipnotice_filepath, df_shipNotice, idx_label = 'id'): # DB
    if not os.path.exists(shipnotice_filepath):
        print(f'\n{shipnotice_filepath} does not exist, create one now and keep all the crawled data here. ')
        df_shipNotice.to_csv(shipnotice_filepath, index_label=idx_label)
    else:
        print(f'\nAppend the newly crawled rows to {shipnotice_filepath}')
        df_shipNotice_total = pd.read_csv(shipnotice_filepath)
        df_shipNotice_total.set_index(idx_label, inplace=True)
        df_shipNotice_total = pd.concat([df_shipNotice_total, df_shipNotice], ignore_index=True)
        df_shipNotice_total.to_csv(shipnotice_filepath, index_label=idx_label)



def startScrapeBot_byHTMLclass(driver, username, password, url, last_crawled_datetime, date_format, shipnotice_folderpath, brieftest=False, brieftestLoops=40):
    if brieftest:
        print('It is a Brief Test! ')

    
    # opening the website  in chrome.
    # print('Opening iExchangeWeb URL....')
    driver.get(url)
    assert "iExchangeWeb" in driver.title

    loginBox = WebDriverWait(driver, 60).until( \
        EC.presence_of_element_located((By.ID, "login-box")))
    
    # find the id or name or class of
    # username by inspecting on username input
    userNameForm = WebDriverWait(loginBox, 60).until( \
        EC.presence_of_element_located((By.ID, "userName")))
    userNameForm.send_keys(username)
    
    # find the password by inspecting on password input
    passwordForm = WebDriverWait(loginBox, 60).until( \
        EC.presence_of_element_located((By.ID, "password")))
    passwordForm.send_keys(password)
    
    # click on submit
    signin_button = WebDriverWait(loginBox, 60).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#login-box .btn-primary"))
    )
    
    assert signin_button.text == 'Sign In', "error at: assert signin_button.text == Sign in"
    
    signin_button.click()


    # Check Login Result: Wait for either loginError, or successful login to mailbox/inbox
    loginResult = WebDriverWait(driver,60).until(
        lambda d: EC.visibility_of_element_located((By.ID, "login_error"))(d) \
            or EC.url_contains('mailbox/inbox')(d)
    )
    if isinstance(loginResult, bool) and loginResult:
        # New Page: mailbox/inbox
        assert 'mailbox/inbox' in driver.current_url, "url doesn't contain mailbox/inbox..."
        print("Logged In!! \nYour Gorgeous Crawler Agent has Navigated to mailbox!")
    else:
        raise MyLoginError


    # Click on the sentmail_button
    leftside_bar = WebDriverWait(driver, 60).until( \
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/aside[1]')))
    mailbox_button = WebDriverWait(leftside_bar, 60).until( \
        EC.presence_of_element_located((By.XPATH, './/section/ul/li[1]/a')))
    mailbox_button.click()

    sentmail_button = WebDriverWait(leftside_bar, 60).until(
        EC.element_to_be_clickable((By.XPATH, ".//section/ul/li[1]/ul/li[4]/a"))
    )

    assert WebDriverWait(sentmail_button, 60).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "span"), "Sent"), "error at assert: sentmail_button doesnt have text 'Sent'"
    )
    
    sentmail_button.click()
    
    assert WebDriverWait(driver, 60).until(EC.url_contains('mailbox/sent')), "error at: assert url_contains mailbox/sent"
    print('Navigated to Sent mail page!')
    
    # Important......it ran cause of this wait
    assert WebDriverWait(driver, 60).until(
        EC.text_to_be_present_in_element((By.XPATH, "/html/body/div[2]/aside[2]/ol/li[2]"), "Sent")
    ), "Mail/Sent has not appeared in the upperbar"
    
    sentmail_url = driver.current_url
    

    # New page, driver current page redirected! 
    # Inside sent mails, find the rows where Subject="Accepted -Ship Notice....."
    
    # Locate the <tbody> tag where the table is at, and get all the rows. 
    table = WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/aside[2]//section[@class='content']//table"))
    )
    tbody = WebDriverWait(table, 60).until(
        EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
    )    
    rows = WebDriverWait(tbody, 60).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, 'tr'))
    )
    print(f'Got all rows in current page! row count={len(rows)}')

    # Out of all the rows, find the "un-crawled" rows:  within the specified date AND is a 'ship notice'
    ship_notice_idx=[]    
    for i, row in enumerate(rows):
        print(f'getting uncrawled row {i}....')
        if brieftest and i==brieftestLoops: break

        creation_date_str = WebDriverWait(row, 60).until( \
            EC.presence_of_element_located((By.XPATH, "./td[11]"))).text
        creation_date = parse_creation_date(creation_date_str, date_format)
        if last_crawled_datetime >= creation_date:
            print('last_crawled_datetime >= creation_date. done. ')
            break
        print(f'found and parsed creation_date_str: {creation_date}')
        subject_str = WebDriverWait(row, 60).until( \
            EC.presence_of_element_located((By.XPATH, "./td[10]"))).text
        
        if subject_str.startswith('Accepted -Ship Notice'):
            print(f'Got subject: {subject_str}')
            ship_notice_idx.append(i)
        else: continue
    
    # In each un-crawled ship notice, click on its "view" folder-like button and get data from classes = 'caption', 'data'. 
    redflag=0
    df_shipNotice = pd.DataFrame()
    print(f'Detected {len(ship_notice_idx)} ship notices at rows = {ship_notice_idx}....')
    
    for idx in reversed(ship_notice_idx): # reversed, start processing from earliest non-crawled date.
        # To avoid stale element exception, find all rows everytime.
        assert WebDriverWait(driver, 60).until(EC.url_contains('mailbox/sent')), "error at (avoid stale element exception): assert url_contains mailbox/sent"
        print('Navigated to Sent mail page!')

        table = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/aside[2]//section[@class='content']//table"))
        )
        tbody = WebDriverWait(table, 60).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
        )
        rows = WebDriverWait(tbody, 60).until(
            EC.visibility_of_all_elements_located((By.TAG_NAME, 'tr'))
        )       
        
        # click on View Button and direct to EDI item page. 
        print(f'Start processing row {idx}')
        row = rows[idx]
        try:
            # Access through relative XPATH
            view_button = WebDriverWait(row, 60).until(
                EC.element_to_be_clickable((By.XPATH, './td[14]/button[1]'))
            )
            view_button.click()
        except ElementClickInterceptedException:
            # Click using JavaScript as a fallback
            print('Click using JavaScript as a fallback')
            driver.execute_script("arguments[0].click();", view_button)

        # Make sure that the navigated EDI item page is normal. 
        # checks url, section element's presence

        assert WebDriverWait(driver, 60).until(
                EC.url_contains('mailbox/item')
        ), "url doesnt contain 'mailbox/item'"
        assert WebDriverWait(driver, 60).until( \
            EC.visibility_of_all_elements_located((By.XPATH, "/html/body/div[2]/aside[2]/section"))
        ), "section XPATH not all elements are not visible"
        
        print('Navigated to EDI item page! ')

        # Get the desired data
        print('Crawling data in a single ship notice...')
        try:
            # Need to Switch to iFrame first, because all the data (#document) is in under an iframe! 
            # Find the iframe element by id
            iframe_locator = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.ID, 'contentFrame'))
            )
            assert iframe_locator is not None, "iframe with ID 'contentFrame' not found"
            
            # Switch to the iframe context
            WebDriverWait(driver, 60).until(
                # If the frame is available it switches the given driver to the specified frame.
                EC.frame_to_be_available_and_switch_to_it(iframe_locator)
            )

            # driver now represents iframe
            ship_notice_body = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '/html/body'))
            )
            
            # get all tables
            tables = WebDriverWait(ship_notice_body, 60).until(
                EC.presence_of_all_elements_located((By.XPATH, './table'))
            )
            assert tables is not None, "tables in ship_notice_body are not found!"

            # start retrieving desired data in current row/ship_notice
            sharedAttr_dict = dict()
            print(f'Total tables count = {len(tables)}')
            for j, table in enumerate(tables):
                print(f'get Table {j}')
                if j==0:
                    ship_notice_title = WebDriverWait(table, 60).until(
                        EC.presence_of_element_located((By.XPATH, './tbody/tr[1]/td/h1'))
                    ).text
                    print(f'Title: {ship_notice_title}')
                
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
                        assert 'ship_to' in sharedAttr_dict.keys(), "'ship_to' key not found in sharedAttr_dict"

                    elif upperlefmost_caption == "Ship Notice #":
                        # get all elements with "caption" classes in the table.tbody element (table.tbody)
                        all_caption_elements = WebDriverWait(table, 60).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "caption"))
                        )
                        target_attr_count=0
                        for caption_element in all_caption_elements:
                            print(f'Ship Notice # captions  =  {caption_element.text}')
                            if caption_element.text.strip() == 'Ship Notice #':
                                # find sibling (data)
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                sharedAttr_dict['ship_notice_num'] = data_element.text
                                target_attr_count+=1
                            elif caption_element.text.strip() == 'Create Date/Time':
                                # find sibling (data)
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                sharedAttr_dict['create_datetime'] = data_element.text
                                target_attr_count+=1
                            elif target_attr_count==2: break
                        assert 'ship_notice_num' in sharedAttr_dict.keys(), "'ship_notice_num' key not found in sharedAttr_dict"
                        assert 'create_datetime' in sharedAttr_dict.keys(), "'create_datetime' key not found in sharedAttr_dict"
                    elif upperlefmost_caption == "Container Type": 
                        continue
                    elif "Order #" in upperlefmost_caption or "PO #" in upperlefmost_caption: # items
                        itemAttr_dict = {}
                        all_caption_elements = WebDriverWait(table, 60).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "caption"))
                        )
                        target_attr_count=0
                        for caption_element in all_caption_elements:
                            print(f'Order #, PO # captions  =  {caption_element.text}')
                            caption = caption_element.text
                            if "Order #" in caption or "PO #" in caption:
                                # find sibling (data)
                                
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                print(f'yay Im in Order # and PO #!!!\ndata={data_element.text}' )
                                if 'Order #' in caption:
                                    # itemAttr_dict['order_type'] = 'Buyer'
                                    itemAttr_dict['order_num'] = data_element.text
                                else: # PO num
                                    # itemAttr_dict['order_type'] = 'Purchase'
                                    itemAttr_dict['order_num'] = data_element.text[:6] # first 6 digits                             
                                target_attr_count+=1
                            elif 'Buyer Part #' in caption: 
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                itemAttr_dict['buyer_part_num'] = data_element.text
                                target_attr_count+=1
                            elif 'Ship Quantity' in caption: 
                                data_element = WebDriverWait(caption_element, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "following-sibling::td[@class='data']"))
                                )
                                itemAttr_dict['ship_quantity'] = data_element.text
                                target_attr_count+=1
                            elif target_attr_count==3:
                                break
                        assert 'order_num' in itemAttr_dict.keys(), "'order_num' key not found in itemAttr_dict"
                        # assert 'order_type' in itemAttr_dict.keys(), "'order_type' key not found in itemAttr_dict"
                        assert 'buyer_part_num' in itemAttr_dict.keys(), "'buyer_part_num' key not found in itemAttr_dict"
                        assert 'ship_quantity' in itemAttr_dict.keys(), "'ship_quantity' key not found in itemAttr_dict"
                        
                        # combine a attributes for a single item at a column level
                        df_row = pd.DataFrame.from_dict([{**sharedAttr_dict, **itemAttr_dict}])
                        # concat items to a allItems ship notice list at a row level
                        df_shipNotice = pd.concat([df_shipNotice, df_row], ignore_index=True)
                    else:
                        print(f'dont need to use table {upperlefmost_caption} right now...')
                    
            # single data row looks like {
            #     "ship_to": "Location A",
            #     "ship_notice_num": "12345",
            #     "create_datetime": "2024-07-10 05:32:00",
            #     "order_num": "54321",
            #     "order_type": "Purchase or Buyer"
            #     "buyer_part_num": "67890",
            #     "ship_quantity": 100
            # }

        except Exception as e:
            print('\nException occured when crawling data, saving to temporary csv...')
            redflag=1
            if df_shipNotice:
                tmpfilepath=os.path.join(shipnotice_folderpath, f'ship-notice-TEMP-{datetime.today().date()}_{datetime.today().hour}_{datetime.today().minute}.csv')
                df_shipNotice.to_csv(os.path.join(os.getcwd(), tmpfilepath))
            raise MyShipNoticeCrawlingError(f"\nShipNotice crawling error. Error message={e}\
                                            \nThere could be new ship notices added in the mean time and shifted the table. \
                                            \nWait and try again. Make sure the crawling time is mostly during non-shipping hours. \
                                            \nOr else, contact support. ")

        # switch back to main mailbox page
        driver.get(sentmail_url)
    
    if not redflag:
        return df_shipNotice



if __name__=="__main__":    
    driver=None
    df_shipNotice=None
    try:
        try:
            # Setup Selenium Docker Environment
            check_docker_installed()
            
            selenium_url = 'http://localhost:7900/?autoconnect=1&resize=scale&password=secret'

            # Stop container first if previous execution failed to stop selenium docker. 
            if is_selenium_server_up(selenium_url):   
                selenium_docker_ctrl('stop')
            
            selenium_docker_ctrl('start')
            wait_until_selenium_server_up(selenium_url, timeout=60)
        except:
            raise RuntimeError('Selenium Docker Environment Setup not completed yet. ')

        # Start Selenium Web Driver
        driver = init_webdriver(timeout=60)
        if driver is not None:
            print("Driver is on!")

        # Set date format of 'creation_date' in iExchangeWeb
        date_format = "%m/%d/%Y %I:%M %p"
        # Create shipnotices folder to save the crawled data
        shipnotice_foldername = 'shipnotices'
        shipnotice_filename = 'ship-notice-total.csv'
        shipnotice_folderpath = os.path.join(os.getcwd(), shipnotice_foldername)
        if not os.path.exists(shipnotice_folderpath):
            # If it doesn't exist, create the folder
            os.makedirs(shipnotice_folderpath)
            print(f'Created folder: ./{shipnotice_foldername}')
        shipnotice_filepath=os.path.join(shipnotice_folderpath, shipnotice_filename)
        last_crawled_datetime = get_last_crawled_datetime(shipnotice_filepath) # ship-notice-total.csv

        while True:
            try:
                # Enter below your login credentials
                # username = input('\nEnter iExchangeWeb username: ')
                # password = maskpass.askpass('Enter iExchangeWeb password: ')
                username, password = get_credentials()

                # URL of the login page of site
                url = "https://www.iexchangeweb.com/ieweb/general/login"
                df_shipNotice = startScrapeBot_byHTMLclass(driver=driver, username=username, password=password, url=url, last_crawled_datetime=last_crawled_datetime, date_format=date_format, shipnotice_folderpath=shipnotice_folderpath, brieftest=False)
                break
            except MyLoginError as e:
                print(f'\n{e}. Username or Password incorrect. \nTry again. (Hit Ctrl-C to Exit)\n')

        assert df_shipNotice is not None, "df_shipNotice is None!"

        save_to_shipnotice_daily(shipnotice_folderpath, df_shipNotice)
        save_to_shipnotice_total(shipnotice_filepath, df_shipNotice)
        print(f"Checkout '{shipnotice_foldername}' folder for all the crawled data")

        
        
    except AssertionError as e:
        print(f'\nIn main try-except block, Assertion Error! {e}')
    except KeyboardInterrupt as e:
        print(f'\nKeyboardInterrupt! {e}')
    except RuntimeError as e:
        print(f'\nIn main try-except block, RuntimeError! {e}')
    except WebDriverException as e:
        print(f'\nIn main try-except block, WebDriverException! {e}')
    except MyShipNoticeCrawlingError as e:
        print(f'\nIn main try-except block, MyShipNoticeCrawlingError! {e}')
    except Exception as e:
        print(f'\nIn main try-except block, General Exception: {e}')
    finally:
        if driver:
            driver.quit()
        selenium_docker_ctrl('stop')
        elapsed_seconds = time.time() - script_run_time
        print(f'script run time = {format_elapsed_seconds(elapsed_seconds)}')
        input("\nPress Enter to exit...")
        print("Have a Nice Day!  (Exiting...)")







