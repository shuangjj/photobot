"""Camera wrapper
"""
import json
import os
import subprocess

from filepicker import FilepickerClient, FilepickerFile

with open('credentials.json') as  f:
    cred = json.load(f)['filestack']
client = FilepickerClient(api_key=cred['apikey'])

def take_photo(delay=0):
    """Take a photo with delay.
    
    The photo will be saved in the photos directory, which is the http server root.

    Args:
        delay (int): Time to wait in second.
    
    Returns:
        FilepickerFile object.

    """
    output_path = "photos/bot.jpg".strip()
    raw_cmd = "fswebcam --jpeg 85 --rotate 180 -F 5 -r 640x480 "
    if delay:
        raw_cmd += " -D {}".format(delay)
    raw_cmd += " " + output_path

    cmd_args = raw_cmd.split()
    with open(os.devnull) as f:
        rc = subprocess.call(cmd_args, stdout=f, stderr=f)
    if rc != 0:
        return -1
    # -$- Upload photo to filestack -$-
    photo = client.store_local_file(output_path)
    return photo

if __name__=="__main__":
    take_photo()
