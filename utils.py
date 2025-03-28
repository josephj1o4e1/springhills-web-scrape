import os, logging, argparse
import logging.handlers as handlers
from datetime import datetime, timedelta
import pandas as pd
import maskpass

def parse_creation_date(datetime_str: str, date_format: str="%m/%d/%Y %I:%M %p") -> datetime:
    # default format example: 6/28/24 11:34 AM
    date_part, time_part, meridiem = datetime_str.split(' ')
    month, day, year = date_part.split('/')
    full_year = f"20{year}"
    new_datetime_str = f"{month}/{day}/{full_year} {time_part} {meridiem}"
    creation_date = datetime.strptime(new_datetime_str, date_format)
    return creation_date

def make_shipfolder():    
    # Create shipnotices folder to save the crawled data
    shipnotice_foldername = 'shipnotices'
    shipnotice_folderpath = os.path.join(os.getcwd(), shipnotice_foldername)
    if not os.path.exists(shipnotice_folderpath):
        # If it doesn't exist, create the folder
        os.makedirs(shipnotice_folderpath)
        print(f'Created folder: ./{shipnotice_foldername}')
    return shipnotice_folderpath

def name_shipfile(crawluntil_time:datetime):
    current_time = datetime.now()    
    formatted_current_time = current_time.strftime("%Y%m%d-%H%M%S") # Format it into the desired string: YYYYMMDD-HHMMSS
    formatted_crawluntil_time = crawluntil_time.strftime("%Y%m%d")
    shipnotice_filename = f'ship-notices-{formatted_current_time}-{formatted_crawluntil_time}.csv'
    return shipnotice_filename

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

def setup_logger():
    logfolder = 'logs'
    logfilename = 'app.log'
    logfolder_path = os.path.join(os.getcwd(), logfolder)

    # Create log folder if it doesn't exist
    if not os.path.exists(logfolder_path):
        os.makedirs(logfolder_path)

    logfile_path = os.path.join(logfolder_path, logfilename)

    # Set up the logger
    logger = logging.getLogger(__name__)  # Use the module's name as logger name
    if not logger.hasHandlers():  # Prevent duplicate handlers when logging is called multiple times
        handler = handlers.RotatingFileHandler(logfile_path, maxBytes=5 * 1024 * 1024, backupCount=3)  # 5 MB per file, 3 backups
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    return logger

def read_cli_arguments():
    # Create the argument parser
    arg_parser = argparse.ArgumentParser(description="Selenium crawler script")

    # Add the environment argument
    arg_parser.add_argument("--env", default="prod", choices=["prod", "dev", "test"], help="Environment to run in")
    args, _ = arg_parser.parse_known_args()

    return args

def get_userinput_cli():
    username = input('\nEnter iExchangeWeb username: ')
    password = maskpass.askpass('Enter iExchangeWeb password: ')
    print('Enter the year/month/day to crawl until...')
    crawl_year = input('Year(ex: 2024) = ')
    crawl_month = input('Month(ex: 1~12) = ')
    crawl_day = input('Day(ex: 1~31) = ')

    return username, password, crawl_year, crawl_month, crawl_day

def store_shipnotice_csv(df_shipNotice: pd.DataFrame, shipnotice_filepath: str, idx_label:str='id'):
    if len(df_shipNotice)>0:
        df_shipNotice.to_csv(shipnotice_filepath, index_label=idx_label)
    else:
        print('No ship notice crawled!')















