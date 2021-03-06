#!/usr/bin/python3
import requests
import os
import mimetypes
import sys
import datetime
import time
import settings

from amscommon import read_config

file = sys.argv[1]
config = read_config()
motion_frames = sys.argv[2]
cons_motion = sys.argv[3]
color = sys.argv[4]
straight_line = sys.argv[5]
bp_frames = sys.argv[6]
meteor_yn = sys.argv[7]
# UPLOAD LATEST CAM FRAME (every hour)

api_key = config['api_key']
device_id  = config['device_id']
url = settings.API_SERVER + "members/api/cam_api/log_motion_capture"
stat = os.stat(file)
#print (stat)
#datetime = stat.st_birthtime
dt = datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
 
# usage: python upload.py type misc_info datetime filename 
# ex: python upload_motion.py ./test_data/20170622132712.jpg 0 1 2 3 4 0

  
#datetime = sys.argv[1]
#misc_info = sys.argv[2]

# The File to send
_file = {'file_data': open(file, 'rb')}

# The Data to send with the file
_data= { 
   'api_key': api_key, 
   'device_id': device_id, 
   'datetime': dt, 
   'format' : 'json',
   'motion_frames': motion_frames,
   'cons_motion':  cons_motion,
   'color':  color,
   'straight_line':  straight_line,
   'bp_frames':  bp_frames,
   'meteor_yn':  meteor_yn,
}
 
session = requests.Session()
del session.headers['User-Agent']
del session.headers['Accept-Encoding'] 

print(url)
print(_data)
print(_file)


with requests.Session() as session:
   response = session.post(url, data= _data, files=_file)


print (response.text)
response.raw.close()