import os
import subprocess
import maskpass

# def set_env_var(key, value):
#     # Set environment variable permanently
#     if os.name == 'nt':  # Windows
#         subprocess.run(['setx', key, value], shell=False)
#     else:  # macOS/Linux
#         # This will only work for the current session, modify shell profile for permanent setting
#         subprocess.run(['export', f'{key}={value}'], shell=False)

def user_entered_credentials():
    username = input('\nEnter iExchangeWeb username: ')
    password = maskpass.askpass('Enter iExchangeWeb password: ')
    
    # while True:
    #     save = input('Do you want to save these credentials in your machine for fast login next time? (y/n): ')
    #     if save.lower() == 'y':
    #         set_env_var('IWEBEX_USERNAME', username)
    #         set_env_var('IWEBEX_PASSWORD', password)
    #         print('Credentials saved. ')
    #         break
    #     elif save.lower() == 'n':
    #         print("Fair choice. You will need to enter your credentials again next time. ")
    #         break
    #     else:
    #         print("please only enter 'y' or 'n'")
    return username, password

def get_credentials():
    # username = os.getenv('IWEBEX_USERNAME')
    # password = os.getenv('IWEBEX_PASSWORD')

    # if username and password:
    #     while True:
    #         use_saved = input("Use saved credentials? (enter 'y' to use saved credentials, enter 'n' to enter credentials again): ")
    #         if use_saved.lower() == 'y': 
    #             print('OK!')   
    #             return username, password
    #         elif use_saved.lower() == 'n':
    #             return user_entered_credentials()
    #         else: 
    #             print("please only enter 'y' or 'n'")
    # else:
    #     return user_entered_credentials()

    return user_entered_credentials()

if __name__ == "__main__":
    username, password=get_credentials()
    print(username)
