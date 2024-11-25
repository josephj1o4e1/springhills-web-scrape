This is a Python Selenium Crawler for iExchangeWeb.  
It handles login, hitting buttons, navigate and scrape data.  

Development Environment:  
OS: WSL2(ubuntu)  
Virtual Environment: Conda  
Tools used: Docker 26.0.2  

1. Install Docker: https://docs.docker.com/get-docker/
2. Install Miniconda: https://docs.anaconda.com/miniconda/install/
3. Create 3 environment variables in a .env file for this project: DEV_USERNAME, DEV_PASSWORD, DEV_CRAWL_UNTIL
4. Run the script using `python scrape-iWebEx.py --env dev`

You can hit CTRL-C to terminate the python script at anytime. 
