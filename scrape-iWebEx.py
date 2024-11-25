import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import time
from dotenv import load_dotenv

# helper functions
from utils import setup_logger, make_shipfolder, name_shipfile, read_cli_arguments, store_shipnotice_csv, get_userinput_cli
from selenium_helper import SeleniumHelper

logger = setup_logger()  # Setup logging
load_dotenv()

def main(args, selhelp: SeleniumHelper):
    app_env = args.env
    # Get username, password, and crawl date
    if app_env=='prod': # input from script argurments (user input from GUI)
        username, password = args.username, args.password
        crawl_year, crawl_month, crawl_day = args.crawl_year, args.crawl_month, args.crawl_day
    elif app_env=='dev': # from environment variables
        username, password = os.environ["DEV_USERNAME"], os.environ["DEV_PASSWORD"]
        crawl_year, crawl_month, crawl_day = os.environ["DEV_CRAWL_YEAR"], os.environ["DEV_CRAWL_MONTH"], os.environ["DEV_CRAWL_DAY"]
    elif app_env=='test': # input from cli
        username, password, crawl_year, crawl_month, crawl_day = get_userinput_cli()
    # Check if any essential inputs is null
    if not username or not password or not crawl_year or not crawl_month or not crawl_day:
        raise ValueError('username or password or crawl date is abnormal!')
    # Check validity of date:
    try:
        crawluntil_time = datetime(year=int(crawl_year), month=int(crawl_month), day=int(crawl_day))
    except ValueError as e:
        logger.error(f"Error occurred during validity of date: {e}")
        print('Invalid date...')
        return

    print(f"Hi {username}, I see you want to crawl from today to {crawluntil_time}. No Problem...")
    
    shipnotice_folderpath = make_shipfolder() # make folder and return folder name
    shipnotice_filename = name_shipfile() # only return file name
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
        print('WebDriver initialization failed, it happens...you can try again or restart machine.')
        return

    if selhelp.driver is None:
        logger.error("WebDriver not initialized.")
        raise RuntimeError("Driver not initialized.")

    print("Driver is on!")

    # Perform login and other operations
    try:
        url = "https://www.iexchangeweb.com/ieweb/general/login"
        selhelp.login_iExWeb(url, username, password)
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

    # Start crawling shipnotices (across pages)
    try:
        df_shipNotice = selhelp.crawl_shipnotices_until(crawluntil_time=crawluntil_time, maxpages=5)
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

