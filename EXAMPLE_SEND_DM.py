from instagram_dm import User

profile_name = ""
DEBUG = False


user = User(profile_name=profile_name, debug=DEBUG)


TO_USER = ""
MSG = ""

user.send_msg(to_username=TO_USER, msg=MSG)