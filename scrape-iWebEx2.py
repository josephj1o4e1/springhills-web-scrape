import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import time

# helper functions
from utils import setup_logger, make_shipfolder, make_shipfile, parse_creation_date, format_elapsed_seconds
from selenium_helper import SeleniumHelper

def main():
    logger = setup_logger()  # Setup logging
    script_start_time = time.time()
    
    df_shipNotice = None
    shipnotice_folderpath = make_shipfolder()
    shipnotice_filename = make_shipfile()

    selhelp = SeleniumHelper(script_start_time)
    
    # Setup selenium environment
    try:
        selhelp.setup_selenium_env()
    except Exception as e:
        logger.error(f"Error occurred during Selenium Docker setup: {e}")
        print('Something went wrong...')
        return  # Exit gracefully

    # Start WebDriver
    try:
        selhelp.init_webdriver(timeout=60)
    except Exception as e:
        logger.error(f"Error occurred while initializing WebDriver: {e}")
        print('WebDriver initialization failed...')
        return

    if selhelp.driver is None:
        logger.error("WebDriver not initialized.")
        raise RuntimeError("Driver not initialized.")

    print("Driver is on!")

    # Perform login and other operations
    try:
        url = "https://www.iexchangeweb.com/ieweb/general/login"
        selhelp.login_iExWeb(url)
    except KeyboardInterrupt as e:
        logger.error(f"Keyboard interrupted: {e}")
        print('\nProcess interrupted by user.')
        return
    except Exception as e:
        logger.error(f"Error occurred during login: {e}")
        print('Login failed...')
        return

    # Navigate to sentmail page...
    
    # Ensure proper cleanup
    finally:
        selhelp.quit_scraper()

if __name__=="__main__":
    main()
