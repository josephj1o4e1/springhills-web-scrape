import os
from datetime import datetime, timedelta

def parse_creation_date(datetime_str: str) -> datetime:
    # Set date format of 'creation_date' in iExchangeWeb
    date_format = "%m/%d/%Y %I:%M %p"
    # 6/28/24 11:34 AM => 6/28/2024 11:34 AM
    date_part, time_part, meridiem = datetime_str.split(' ')
    month, day, year = date_part.split('/')
    full_year = f"20{year}"
    new_datetime_str = f"{month}/{day}/{full_year} {time_part} {meridiem}"
    creation_date = datetime.strptime(new_datetime_str, date_format)
    return creation_date

def make_shipfolder(shipnotice_foldername):    
    # Create shipnotices folder to save the crawled data       
    shipnotice_folderpath = os.path.join(os.getcwd(), shipnotice_foldername)
    if not os.path.exists(shipnotice_folderpath):
        # If it doesn't exist, create the folder
        os.makedirs(shipnotice_folderpath)
        print(f'Created folder: ./{shipnotice_foldername}')

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

