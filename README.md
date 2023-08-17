# Instagram Direct Message Bot

This script provides a way to automate sending direct messages on Instagram using the Selenium library in Python. The script supports logging in with two-factor authentication and utilizes a custom User class to manage the user account.

## Dependencies

To use this script, you need to have the following Python packages installed:

    selenium
    undetected-chromedriver
    requests

You can install them using the following command:

    pip3 install selenium undetected-chromedriver requests

## Usage - Check Examples Folder

Import the User class from the script:
````py
from instagram_web import User
````

Create an instance of the User class and an linked chrome profile:

````py
user = User(profile_name="ACC PROFILE NAME", debug=False)
````

You have to log in to your Instagram account by yourself but you can access it starting again with same profile name:


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

## Notes
If you have any questions or feedback feel free to contact me.

This script is provided for educational purposes only. Automating actions on Instagram may violate their terms of service, and your account may be subject to restrictions or bans. Use this script at your own risk.


