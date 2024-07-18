import os
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, WebDriverException
from selenium_docker_ctrl import selenium_docker_ctrl

from datetime import datetime
import pandas as pd
import time
import requests


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
            print(f'driver not yet initialized, please WAIT until timeout={timeout} seconds.')
            time.sleep(poll_interval)
    else:
        raise RuntimeError("Selenium server did not start within the timeout period.")

def parse_creation_date(datetime_str: str) -> datetime:
    # 6/28/24 11:34 AM => 6/28/2024 11:34 AM
    date_part, time_part, meridiem = datetime_str.split(' ')
    month, day, year = date_part.split('/')
    full_year = f"20{year}"
    new_datetime_str = f"{month}/{day}/{full_year} {time_part} {meridiem}"
    date_format = "%m/%d/%Y %I:%M %p"
    creation_date = datetime.strptime(new_datetime_str, date_format)
    return creation_date



def startScrapeBot_byHTMLclass(driver, username, password, url, last_crawled_datetime, brieftest=False, brieftestLoops=40):
    print('Start scrape bot byHTMLclass....')
    if brieftest:
        print('It is a Brief Test! ')

    
    # opening the website  in chrome.
    print('Opening URL....')
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

    # New Page: mailbox/inbox
    assert WebDriverWait(driver, 60).until(EC.url_contains('mailbox/inbox')), "error at assert: mailbox_url doesnt contain mailbox/inbox"
    print("Now in mailbox!")

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
    print(f'got all rows! row count={len(rows)}')

    # Out of all the rows, find the "un-crawled" rows:  within the specified date AND is a 'ship notice'
    ship_notice_idx=[]    
    for i, row in enumerate(rows):
        print(f'getting uncrawled row {i}....')
        if brieftest and i==brieftestLoops: break

        creation_date_str = WebDriverWait(row, 60).until( \
            EC.presence_of_element_located((By.XPATH, "./td[11]"))).text
        creation_date = parse_creation_date(creation_date_str)
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
    print(f'crawled ship notices at rows = {ship_notice_idx}....')
    
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

        print(f'rows count = {len(rows)}')        
        
        # click on View Button and direct to EDI item page. 
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
            print('Exception occured when crawling data, saving to temporary csv...')
            redflag=1
            df_shipNotice.to_csv(f'./shipnotices/ship-notice-TEMP-{datetime.today().date()}_{datetime.today().hour}_{datetime.today().minute}.csv')
            raise e

        # switch back to main mailbox page
        driver.get(sentmail_url)
        
    if not redflag:
        return df_shipNotice



if __name__=="__main__":
    selenium_docker_ctrl('start')

    wait_until_selenium_server_up('http://localhost:7900/?autoconnect=1&resize=scale&password=secret', timeout=60)

    # Enter below your login credentials
    ***REMOVED***
    ***REMOVED***

    # URL of the login page of site
    # which you want to automate login.
    url = "https://www.iexchangeweb.com/ieweb/general/login"

    # Get the "new data": last datetime of crawled data ~ newest
    date_format = "%m/%d/%Y %I:%M %p"
    last_crawled_datetime = datetime.strptime("7/17/2024 12:00 AM", date_format)

    driver=None
    try:
        driver = init_webdriver(timeout=60)
        if driver is not None:
            print("Driver is on!")

        df_shipNotice = startScrapeBot_byHTMLclass(driver=driver, username=username, password=password, url=url, last_crawled_datetime=last_crawled_datetime, brieftest=False)
        assert df_shipNotice is not None, "df_shipNotice is None!"
        df_shipNotice.to_csv(f'./shipnotices/ship-notice-{datetime.today().date()}_{datetime.today().hour}_{datetime.today().minute}.csv', index_label='id')
        last_crawled_datetime = datetime.today()
        print(f'last_crawled_datetime={last_crawled_datetime}')
    except AssertionError as e:
        print(f'main block, Assertion Error! {e}')
    except KeyboardInterrupt as e:
        print(f'main block, KeyboardInterrupt! {e}')
    except WebDriverException as e:
        print(f'main block, WebDriverException! {e}')
    except Exception as e:
        print(f'main block, General Exception: {e}')
    finally:
        if driver:
            driver.quit()
        selenium_docker_ctrl('stop')






