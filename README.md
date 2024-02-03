# Instagram Direct Message Bot

This script provides a way to automate certain actiivties on Instagram i.e. sending direct messages.
Support for chrome profiles - automatic logging in and manual logging in.

## Dependencies

To use this script, you need to have the following Python packages installed:

    selenium
    pyotp

You can install them using the following command:

    pip3 install selenium pyotp

## Basic usage

Import the User class from the script:
````py
from instagram_web import User
````

Create an instance of the User class:

````py
 #To use chrome profiles
user = User(profile_name="profile_name", debug=False)                                                      

 #To use it to login automatically
user = User(username="your_username",password="your_password",token="your_2fa_token(optional)", debug=False)   

#To use both chrome profiles and aoutomatic login  
user = User(profile_name="profile_name",username="your_username",password="your_password",token="your_2fa_token(optional)", debug=False)

#You dont have to use profiles or automatic login but you would have to login every time by yourself
user = User(debug=False)    
````


#
Send a direct message to another user:
```py
user.send_msg(to_username="recipient_username", msg="Your message here")
````
Send a direct message to another user knowing his msg_id:
```py
user.send_msg_to_msg_id(msg_id="recipient_msg_id", msg="Your message here")
````


Get session cookies (may use for a requesting directly from instagram api)
````py
cookies = user.get_cookies(close_after=True)
````

## Notes
If you have any questions or feedback feel free to contact me.

This script is provided for educational purposes only. Automating actions on Instagram may violate their terms of service, and your account may be subject to restrictions or bans. Use this script at your own risk.


