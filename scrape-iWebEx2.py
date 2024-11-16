import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import time

# helper functions
from utils import setup_logger, make_shipfolder, make_shipfile, read_cli_arguments, store_shipnotice_csv, parse_creation_date, format_elapsed_seconds
from selenium_helper import SeleniumHelper

def main(args):
    app_env = args.env
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
        selhelp.login_iExWeb(url, app_env)
    except KeyboardInterrupt as e:
        logger.error(f"Keyboard interrupted: {e}")
        print('\nProcess interrupted by user.')
        return
    except Exception as e:
        logger.error(f"Error occurred during login: {e}")
        print('Login failed...')
        return

    # Navigate to sentmail page...
    try:
        selhelp.navigate_sentmail()
    except Exception as e:
        logger.error(f"Error occurred during navigating to sentmail page: {e}")
        print('Something went wrong when navigating to the sentmail page, sorry...')
        return

    # Within single page, find the rows where Subject="Accepted -Ship Notice....."
    try:
        shipnotice_idxs = selhelp.get_shipnotice_idxs(app_env)
    except Exception as e:
        logger.error(f"Error occurred at getting ship notice indexes: {e}")
        print('Something went wrong when crawling the shipnotices, sorry...')
        return
    
    # Start crawling shipnotices (Within single page)
    try:
        df_shipNotice = selhelp.crawl_shipnotices(shipnotice_idxs, app_env)
        assert df_shipNotice is not None
    except Exception as e:
        logger.error(f"Error occurred at crawl_shipnotices: {e}")
        print('Something went wrong when crawling the shipnotices, sorry...')
        return
    
    # Store DataFrame
    try:
        store_shipnotice_csv(df_shipNotice)
    except Exception as e:
        logger.error(f"Error occurred at store_shipnotice_csv: {e}")
        print('Something went wrong when storing the shipnotices, sorry...')
        return
    
    # Ensure proper cleanup
    finally:
        selhelp.quit_scraper()

if __name__=="__main__":
    args = read_cli_arguments()
    main(args)
