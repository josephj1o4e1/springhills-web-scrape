import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import time

# helper functions
from utils import setup_logger, make_shipfolder, name_shipfile, read_cli_arguments, store_shipnotice_csv
from selenium_helper import SeleniumHelper

logger = setup_logger()  # Setup logging

def main(args, selhelp: SeleniumHelper):
    app_env = args.env
    shipnotice_folderpath = make_shipfolder() # make and name
    shipnotice_filename = name_shipfile() # only name
    shipnotice_filepath = os.path.join(shipnotice_folderpath, shipnotice_filename)
    
    # Setup selenium environment
    try:
        selhelp.setup_selenium_env()
    except Exception as e:
        logger.error(f"Error occurred during Selenium Docker setup: {e}")
        print('Something went wrong...')
        return

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
    except Exception as e:
        logger.error(f"Error occurred during login: {e}")
        print('Login failed...')
        return

    print('Locating ship notice data...')

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
        logger.info(shipnotice_idxs)
        logger.info(f"len={len(shipnotice_idxs)}")
    except Exception as e:
        logger.error(f"Error occurred at getting ship notice indexes: {e}")
        print('Something went wrong when crawling the shipnotices, sorry...')
        return
    
    # print(f'Found {len(shipnotice_idxs)} rows with ship notices at page {page} starting from row {max(shipnotice_idxs)} to {min(shipnotice_idxs)}.')
    print(f'Found {len(shipnotice_idxs)} rows with ship notices at page 1. \nstarting from row {max(shipnotice_idxs)} to {min(shipnotice_idxs)}.')

    # Start crawling shipnotices (Within single page)
    try:
        df_shipNotice = selhelp.crawl_shipnotices(shipnotice_idxs, app_env)
        expected_cols = ["ship_to","ship_notice_num","order_num","buyer_part_num"]
        if list(df_shipNotice.columns)!=expected_cols:
            raise ValueError(f"Schema mismatch! Expected {expected_cols}, but got {list(df_shipNotice.columns)}")
    except ValueError as e:
        logger.error(f"Error occurred at crawl_shipnotices: {repr(e)}")
        print('Something went wrong when crawling the shipnotices, sorry...')
        return
    except Exception as e:
        logger.error(f"Error occurred at crawl_shipnotices: {repr(e)}")
        print('Something went wrong when crawling the shipnotices, sorry...')
        return
    
    # Store DataFrame
    try:
        store_shipnotice_csv(df_shipNotice, shipnotice_filepath)
    except Exception as e:
        logger.error(f"Error occurred at store_shipnotice_csv: {repr(e)}")
        print('Something went wrong when storing the shipnotices, sorry...')
        return
    print("Saved data to shipnotice folder!")
    logger.info(f"total time spent: {(time.time()-script_start_time):.2f}s")



if __name__=="__main__":
    args = read_cli_arguments()
    script_start_time = time.time()
    selhelp = SeleniumHelper(script_start_time)
    try:
        main(args, selhelp)
    except KeyboardInterrupt as e:
        logger.info(f"Keyboard interrupted by user.")
        print('\nProcess interrupted by user.')
    except Exception as e:
        logging.error(f"Unhandled exception in main: {e}")
    finally:
        # Ensure proper cleanup and exit gracefully
        selhelp.quit_scraper()

