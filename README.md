# Instagram Direct Message Bot

This script provides a way to automate sending direct messages on Instagram.

Support for chrome profiles with automatic logging in.

## Dependencies (for python 3.11)

To use this script, you need to have the following Python packages installed:

    undetected_chromedriver
    selenium
    requests
    pyotp

You can install them using the following command:

    pip3 install selenium pyotp undetected_chromedriver requests

## Basic usage

### Import the User class from the script:
````py
from instagram_web import User
````


### Create an instance of the User class:

Basic Example (with Chrome profile and credentials):
````py
user = User(
    profile_name="myprofile",
    username="my_instagram_username",
    password="my_instagram_password"
)
````

Using Two-Factor Authentication (2FA):
```py
user = User(
    username="my_instagram_username",
    password="my_instagram_password",
    token="my_totp_token"
)
```


Running in Headless Mode:
```py
user = User(
    username="my_instagram_username",
    password="my_instagram_password",
    headless=True
)
```

Using a non auth Proxy:
```py
user = User(
    username="my_instagram_username",
    password="my_instagram_password",
    proxy="http://proxyserver:port"
)
```


Custom Chrome and ChromeDriver Paths:
```py
user = User(
    browser_executable_path="/path/to/chrome",
    driver_executable_path="/path/to/chromedriver"
)
```



### Send a direct message to another user:
```py
user.send_msg(to_username="recipient_username", msg="Your message here", skip_if_already_messaged=False)
````
Send a direct message to another user knowing msg_id:
```py
user.send_msg_to_msg_id(msg_id="recipient_msg_id", msg="Your message here",skip_if_already_messaged=False)
````


### Get session cookies
```py
cookies = user.get_cookies(close_after=False)
```

### Exit driver
```py
user.exit_driver()
```

## Notes
If you have any questions or feedback feel free to contact me.


> [!CAUTION]
> This script is provided for educational purposes only. Automating actions on Instagram may violate their terms of service, and your account may be subject to restrictions or bans. Use this script at your own risk.

