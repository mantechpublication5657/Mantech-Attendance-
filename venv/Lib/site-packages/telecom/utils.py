import re
from twilio.rest import Client
from django.conf import settings
from twilio.base.exceptions import TwilioRestException

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
try:
    ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
    SERVICE_SID = settings.TWILIO_SERVICE_SID
    AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
except AttributeError as e:
    raise Exception("Set attribute....", e)
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_otp(telecom, channel='sms'):
    try:
        verification = client.verify \
            .services(SERVICE_SID) \
            .verifications \
            .create(to=telecom, channel=channel)
        return True
    except TwilioRestException:
        return False


def verify_otp(telecom, code):

    try:
        verification_check = client.verify \
            .services(SERVICE_SID) \
            .verification_checks \
            .create(to=telecom, code=code)
        if verification_check.status == "approved":
            return True
        return False
    except TwilioRestException:
        return False


def send_sms(body, to):
    try:
        message = client.messages.create(
            body=body, from_=settings.TWILIO_PHONE_NUMBER, to=to)
        if message.sid:
            return True
    except TwilioRestException:
        return False
    
    except AttributeError as e:
        raise Exception("Set attribute....", e)


class Mask:
    '''It will manage the telecom related operations.'''

    def apply(self, string, channel):
        if channel == 'email':
            return self.email_mask(string)
        elif channel == 'sms':
            return self.phone_mask(string)

    def phone_mask(self, string, digits_to_keep=3, mask_char='x'):
        '''mask phone number for e.g +91000393939-> xxxxxxx39'''
        num_of_digits = len(string)
        digits_to_mask = num_of_digits - digits_to_keep
        masked_string = re.sub(
            '[+\da-zA-Z]', mask_char, string, digits_to_mask)
        return masked_string

    def email_mask(self, string, mask_char='*****'):
        '''mask email for e.g abcd@gmail.com-> a****d@gmail.com'''
        index = string.find('@')
        return string[0]+mask_char+string[index-1:]

mask = Mask()