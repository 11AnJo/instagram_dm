# instagram-dm
 Selenium based library that automates direct messaging to instagram accounts

## currently not working with any 2-step verification

## How to use

```py
from instagram-dm import initialize_driver, login, send_msg

driver = initialize_driver()
login(driver, username, password)

send_msg(driver,to_username,msg)
```
