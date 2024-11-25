import os
from datetime import datetime
from utils import setup_logger
from core_logic import SeleniumApp
from utils import setup_logger, read_cli_arguments, get_userinput_cli
from dotenv import load_dotenv

logger = setup_logger()  # Setup logging
load_dotenv()


def main(args):
    app_env = args.env
    
    # Get username, password, and crawl date
    if app_env=='prod': # input from script argurments (user input from GUI)
        username, password, crawl_year, crawl_month, crawl_day = get_userinput_cli()
    else: # app_env is 'dev' or 'test': 
        username, password = os.environ["DEV_USERNAME"], os.environ["DEV_PASSWORD"]
        crawl_year, crawl_month, crawl_day = os.environ["DEV_CRAWL_YEAR"], os.environ["DEV_CRAWL_MONTH"], os.environ["DEV_CRAWL_DAY"]
     
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
    
    # Run App
    app = SeleniumApp(username, password, crawluntil_time)
    app.run()



if __name__=="__main__":
    args = read_cli_arguments()
    main(args)
    