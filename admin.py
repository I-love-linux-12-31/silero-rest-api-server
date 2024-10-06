import random
from hashlib import sha256
from logging import getLogger

_admin_password = "<PASSWORD>"


def generate_passwd():
    global _admin_password
    _admin_password = sha256(str(random.randint(13, 128) ** random.randint(1, 6)).encode()).hexdigest()
    print("Admin API KEY:", _admin_password)


def is_valid(passwd):
    print(passwd, _admin_password, sep='\n')
    return _admin_password == passwd
