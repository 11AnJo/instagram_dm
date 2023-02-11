# instagram-dm
 Selenium based library that automates direct messaging to instagram accounts

## currently not working with any 2-step verification

## How to use

1. Download newest geckodriver version from https://github.com/mozilla/geckodriver/releases and drop it to 
2. Install selenium ```pip install selenium```
```py
from instagram_dm import initialize_driver, login, send_msg

driver = initialize_driver()
login(driver, username, password)

send_msg(driver,to_username,msg)
```
