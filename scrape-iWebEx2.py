import sys, os, subprocess
from datetime import datetime, timedelta
import pandas as pd
import time
import requests
import maskpass

# selenium
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, WebDriverException
# helper functions
from utils import make_shipfolder, parse_creation_date, format_elapsed_seconds
from selenium_helper import setup_selenium_env, init_webdriver, login_iExWeb, check_login_status, \
                            MyLoginError, safe_exec_selenium, quit_scraper

script_run_time = time.time()

if __name__=="__main__":    
    driver=None
    df_shipNotice=None
    shipnotice_foldername = 'shipnotices'
    current_time = datetime.now()    
    formatted_time = current_time.strftime("%Y%m%d-%H%M%S") # Format it into the desired string: YYYYMMDD-HHMMSS
    shipnotice_filename = f'ship-notice-total{formatted_time}.csv'
    make_shipfolder(shipnotice_foldername)

    try:
        setup_selenium_env()
    except Exception as e:
        print(f"Error Occurred when setting up Selenium Docker: {e}")
        raise RuntimeError('Selenium Docker Environment Setup not completed. ')
    
    # Start Selenium Web Driver
    driver = init_webdriver(timeout=60)
    if driver is not None:
        print("Driver is on!")

    # Login to iExchangeWeb
    url = "https://www.iexchangeweb.com/ieweb/general/login" # login page of site
    driver.get(url)    
    safe_exec_selenium(login_iExWeb, driver, script_run_time, attempts=3)
    
    # Start Scraping
    



    # assert df_shipNotice is not None, "df_shipNotice is None!"



    # close driver everytime when quitting
    quit_scraper(driver, script_run_time)
