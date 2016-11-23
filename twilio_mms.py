"""Twillo send photo.
"""
import json
import pprint as pp

from twilio.rest import TwilioRestClient 

TEST = False

def send_photo(to, url, test=TEST):
    TEST = test
    """Send photo to user phone number.

    Args:
        to (str): Target phone number.

    """
    creds = {}
    with open('credentials.json') as credential_file:
        creds = json.load(credential_file)['twilio']
    #pp.pprint(creds)

    cred = creds['test'] if TEST else creds['live']
        
    client = TwilioRestClient(cred['sid'], cred['authtoken']) 

    live_num = "+16463628583"
    test_num = "+15005550006"
    my_num = test_num if TEST else live_num

    message = client.messages.create(
        to=to, 
        from_= my_num, 
        body='''Enjoy your photo!
--Photo Bot
    ''', 
        media_url=url
    )

    print(message.sid)

if __name__ == "__main__":
    send_photo("+12153014655", "")
