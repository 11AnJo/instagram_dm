# Instagram Direct Message Bot

This script provides a way to automate sending direct messages on Instagram using the Selenium library in Python. The script supports logging in with two-factor authentication and utilizes a custom User class to manage the user account.

## Dependencies

To use this script, you need to have the following Python packages installed:

    selenium
    pyotp

You can install them using the following command:

    pip install selenium pyotp

## Usage - Check Examples Folder

Import the User class from the script:
````py
from instagram_dm import User
````

Create an instance of the User class, passing your Instagram username and password:

````py
user = User(username="your_username", password="your_password", token="your_2FA_token_if_any", debug=False)
````
If you have two-factor authentication enabled, replace "your_2FA_token_if_any" with your actual 2FA token. Otherwise, set the token parameter to False. Make debug=True if needed.

Log in to your Instagram account:

````py
user.login()
````

Send a direct message to another user:
```py
user.send_msg(to_username="recipient_username", msg="Your message here")
````
Replace "recipient_username" with the actual Instagram username of the recipient.
Replace "Your message here" with the actual message you want to send.


Get session cookies (may use for a requesting directly from instagram api)
````py
cookies = user.get_cookies(close_after=True)
````

## Code Overview

The provided code defines a User class with several methods to manage an Instagram account, including logging in, accepting cookies, handling two-factor authentication, and sending direct messages.

The User class has the following methods:

    __init__(self, username, password, token=False, debug=False, use_chrome=False): Initializes a User instance.
    __initialize_log(self): Initializes a logger for the user account.
    __initialize_driver(self, use_chrome=False): Initializes the Selenium WebDriver.
    __generate_2factor_code(self, token): Generates a two-factor authentication code.
    __accept_cookie(self, driver): Accepts cookies on the Instagram website.
    __two_factor(self): Handles two-factor authentication.
    login(self): Logs in to the user's Instagram account.
    __exit_driver(self): Closes the Selenium WebDriver.
    get_cookies(self, close_after=True): Retrieves cookies for the user's Instagram account.
    __is_element_present(self, xpath, time_to_wait): Checks if an element is present on the page.
    send_msg(self, to_username, msg): Sends a direct message to another user.

The LOCATORS dictionary contains XPath locators for various elements on the Instagram website.

## Notes
If you have any questions or feedback feel free to contact me.

This script is provided for educational purposes only. Automating actions on Instagram may violate their terms of service, and your account may be subject to restrictions or bans. Use this script at your own risk.


