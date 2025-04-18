import time
import pyotp
import hashlib
import uuid

def generate_2factor_code(token: str):
    totp = pyotp.TOTP(token)
    current_time = time.time()
    time_step = 30  # TOTP time step
    remaining_time = time_step - (current_time % time_step)

    # If the code is valid for less than 4 seconds, wait for the next one
    if remaining_time < 4:
        time.sleep(remaining_time)

    return totp.now()

def escape_string_for_xpath(s):
    if '"' in s and "'" in s:
        return 'concat(%s)' % ", '\"',".join('"%s"' % x for x in s.split('"'))
    elif '"' in s:
        return "'%s'" % s
    return '"%s"' % s

def generate_uuid(return_hex=False, seed=None):
    if seed:
        m = hashlib.md5()
        m.update(seed.encode('utf-8'))
        new_uuid = uuid.UUID(m.hexdigest())
    else:
        new_uuid = uuid.uuid1()
    if return_hex:
        return new_uuid.hex
    return str(new_uuid)

