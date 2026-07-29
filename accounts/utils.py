import random
from datetime import datetime
from accounts.models import User

import pyotp
def generate_otp():
   totp = pyotp.TOTP(pyotp.random_base32(), interval=300) # Valid for 5 minutes
   return totp.now()

def verify_otp(otp, user_otp):
   return str(otp).strip() == str(user_otp).strip()

