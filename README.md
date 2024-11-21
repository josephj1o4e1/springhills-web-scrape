Before you run the script, install Docker: https://docs.docker.com/get-docker/   
We need docker because our script utilizes a selenium bot to crawl data, which mimicks human interaction to avoid bot detection. We use the official selenium docker image to setup the selenium bot.   
You can hit CTRL-C to terminate script anytime.  

Create 3 environment variables in a .env file for this project:
DEV_USERNAME, DEV_PASSWORD, DEV_CRAWL_UNTIL


