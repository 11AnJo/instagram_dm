from instagram_dm import User

USERNAME = ""
PASSWORD = ""
_2F_TOKEN = ""
DEBUG = False


user = User(username=USERNAME, password=PASSWORD, token=_2F_TOKEN, debug=DEBUG)
user.login()


TO_USER = ""
MSG = ""

user.send_msg(to_username=TO_USER, msg=MSG)