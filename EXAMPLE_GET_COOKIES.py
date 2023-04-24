from instagram_dm import User

USERNAME = ""
PASSWORD = ""
_2F_TOKEN = ""
DEBUG = False


user = User(username=USERNAME, password=PASSWORD, token=_2F_TOKEN, debug=DEBUG)
user.login()



cookies = user.get_cookies(close_after=True)
print(cookies)