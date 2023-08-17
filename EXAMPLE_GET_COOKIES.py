from instagram_dm import User


profile_name = ""
DEBUG = False


user = User(profile_name=profile_name, debug=DEBUG)




cookies = user.get_cookies(close_after=True)
print(cookies)