LOCATORS = {
    "login": {
        "username_field": "//input[@name='username']",
        "password_field": "//input[@name='password']",
        "error": "//p[@id='slfErrorAlert']",
        "sus_automated_dismiss": "//div/span[text()='Dismiss']",
        "profile_username":"//*[text()='{}']",          #
        "log_in_profile_btn":'//a[@tabindex="0" and text()="Log in"]',
        "suspicious_attempt":"//p[text()='Suspicious Login Attempt']",
        "save_info": "//button[text()='Save info']",
        "freezed":"//span[@dir='auto' and text()='Something went wrong']",
        "2f_screen_present": "//input[@aria-describedby='verificationCodeDescription' and @aria-label='Security Code']",
        "2f_entering_error": "//p[@id='twoFactorErrorAlert' and @role='alert']",
        "cookie_pre_login_accept": "//button[text()='Decline optional cookies']",

    },
    "dm": {
        "msg_field": "//div[@role='textbox' and @aria-label='Message']",
        "send_button": "//div[@role='button' and text()='Send']",
        "error_present": "//*[@aria-label='Failed to send']",
        "account_instagram_user":"//div[@role='presentation']//div//div//div//span[normalize-space(.)='Instagram User' and contains(@style, 'line-height: var(--base-line-clamp-line-height);')]",
        "not_everyone":"//div//div//span[@dir='auto' and contains(text(),'Not everyone can message this account.')]",
        "avatar_src":".//div[@role='presentation']//img[@alt='User avatar']",
        "invite_sent":".//span[contains(text(), 'Invite sent')]",
        "loaded":"//div//span[contains(text(),'Instagram') and @dir='auto']",
        "already_sent": "//div[@role='none']//div[@dir='auto']",
        "user_not_found": "//span[text()='No account found.']",
    },
}

URLS = {
    "login": "https://www.instagram.com/accounts/login/?next=https%3A%2F%2Fwww.instagram.com%2Fdirect%2F",
    "user_info_endpoint": "https://www.instagram.com/api/v1/users/web_profile_info/",
    "hashtag_search_endpoint": "https://www.instagram.com/api/v1/fbsearch/web/top_serp/",
}   
