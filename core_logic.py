import os
import time

# helper functions
from utils import setup_logger, make_shipfolder, name_shipfile, store_shipnotice_csv
from selenium_helper import SeleniumHelper

logger = setup_logger()  # Setup logging

class SeleniumApp:
    def __init__(self, username, password, crawluntil_time):
        self.username = username
        self.password = password
        self.crawluntil_time = crawluntil_time
        self.script_start_time = time.time()
        self.selhelp = SeleniumHelper(script_start_time=self.script_start_time)
    
    def mainapp(self):
        print(f"Hi {self.username}, I see you want to crawl from today to {self.crawluntil_time}. No Problem...")
        
        shipnotice_folderpath = make_shipfolder() # make folder and return folder name
        shipnotice_filename = name_shipfile(self.crawluntil_time) # only return file name
        shipnotice_filepath = os.path.join(shipnotice_folderpath, shipnotice_filename)
        
        # Setup selenium environment
        try:
            self.selhelp.setup_selenium_env()
        except Exception as e:
            logger.error(f"Error occurred during Selenium Docker setup: {e}")
            print('Something went wrong...')
            return

        # Start WebDriver
        try:
            self.selhelp.init_webdriver(timeout=60)
        except Exception as e:
            logger.error(f"Error occurred while initializing WebDriver: {e}")
            print('WebDriver initialization failed, it happens...you can try again or restart machine.')
            return

        if self.selhelp.driver is None:
            logger.error("WebDriver not initialized.")
            raise RuntimeError("Driver not initialized.")

        print("Driver is on!")

        # Perform login and other operations
        try:
            url = "https://www.iexchangeweb.com/ieweb/general/login"
            self.selhelp.login_iExWeb(url, self.username, self.password)
        except Exception as e:
            logger.error(f"Error occurred during login: {e}")
            print('Login failed...')
            return

        print('Locating ship notice data...')

        # Navigate to sentmail page...
        try:
            self.selhelp.navigate_sentmail()
        except Exception as e:
            logger.error(f"Error occurred during navigating to sentmail page: {e}")
            print('Something went wrong when navigating to the sentmail page, sorry...')
            return

        # Start crawling shipnotices (across pages)
        try:
            df_shipNotice = self.selhelp.crawl_shipnotices_until(crawluntil_time=self.crawluntil_time, maxpages=5)
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
        logger.info(f"total time spent: {(time.time()-self.script_start_time):.2f}s")

    def run(self):
        try:
            self.mainapp()
        except KeyboardInterrupt as e:
            logger.info(f"Keyboard interrupted by user.")
            print('\nProcess interrupted by user.')
        except Exception as e:
            logger.error(f"Unhandled exception in main: {e}")
        finally:
            # Ensure proper cleanup and exit gracefully
            self.selhelp.quit_scraper()

        






