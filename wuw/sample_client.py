

import http.client, urllib.parse
import json
import pprint
import os

def send_message(endpoint, message):
	conn = http.client.HTTPConnection("localhost", 18080)
	conn.request("PUT", endpoint, json.dumps(message).encode('utf-8'))
	response = conn.getresponse()
	data = response.read()
	conn.close()
	if response.status != 200:
		print(response, data)
		return False
	else:
		return True

def get_message():
	conn = http.client.HTTPConnection("localhost", 18080)
	conn.request("GET", "/events")
	response = conn.getresponse()
	data = response.read()
	conn.close()

	if response.status != 200:
		print(response, data)
		return None
	else:
		return json.loads(data.decode('utf-8'))

def get_sound_path(filename):
	# get path to sound files that are in the same directory as the python script
	return os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)

def mix_init(tag):
    """Initialize mix client.
    
    Args:
        tag (str): Mix model context tag.

    """
    with open('credentials.json') as f:
        cred_mix = json.load(f)['mix']
        send_message('/configure', {
            "credentials": {
                "app_id": cred_mix['app_id'],
                "app_key": cred_mix['app_key']
            },
            "wakeup": {
                "phrases": [
                    'hey dragon',
                    'hello dragon'
                ],
                "beep": get_sound_path('listen.pcm'),
            },
            "recognition": {
                "context_tag": tag
            }
        })

        send_message('/output/file', {'path': get_sound_path('startup.pcm')})

def normalize_duration(duration_field):                                         
    """ duration normalization.                                                 
                                                                                
    Args:                                                                       
        duration_field (jsonObject): {'literal': _v_, 'value': {'nuance_DURATION_ABS': {'nuance_MINUTE': _v_}}, 'ranges': _v_}
                                                                                
    Returns:                                                                    
        seconds (int): convert to seconds                                       
    """                                                                         
    seconds = 0                                                                 
    duration_value = duration_field.get('value')                                
    if duration_value:                                                          
        duration_abs = duration_value.get('nuance_DURATION_ABS')                
        if duration_abs:                                                        
            if duration_abs.get('nuance_MINUTE'):                               
                seconds = duration_abs.get('nuance_MINUTE') * 60                
            elif duration_abs.get('nuance_SECOND'):                             
                seconds = duration_abs.get('nuance_SECOND')                     
        return seconds       


