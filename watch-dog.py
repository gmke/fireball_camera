#!/usr/bin/python3 

import subprocess
import datetime
import os
import time

import sendgrid
from sendgrid.helpers.mail import *
from amscommon import read_config
import psutil

def clean_zombies():
   kill_zombies("sro-settings.py", 10)
   kill_zombies("examine-still.py", 60)
   kill_zombies("stack-runner.py", 60)
   kill_zombies("PV.py", 60)
   kill_zombies("fast_frames5.py", 60)
   kill_zombies("auto-brightness.py", 60)

def kill_zombies(process_name, tlimit):
   for p in filter_by_name(process_name):
      diff = time.time() - p.create_time()
      min = int(diff/60)
      print ("found", p.cmdline(), p.pid, min, " minutes")
      if min > tlimit:
         print("Killing:", p.pid, p.name())
         os.system("kill -9 " + str(p.pid))
      

def filter_by_name(process_name):
    for process in psutil.process_iter():
        try:
            #print(process.name)
            if process_name in str(process.cmdline()) :
                yield process
        except psutil.NoSuchProcess:
            pass


def sendmail(tom, frm, subject, msg):
   sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
   from_email = Email(tom)
   to_email = Email(frm)
   content = Content("text/html", msg)
   mail = Mail(from_email, subject, to_email, content)
   response = sg.client.mail.send.post(request_body=mail.get())
   print(response.status_code)
   print(response.body)
   print(response.headers)

def check_disk_space():
   derrs = []
   cmd = "df -H | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{ print $5 \" \" $1 }'"
   output = subprocess.check_output(cmd, shell=True).decode("utf-8")
   lines = output.split("\n")
   for line in lines:
      line = line.replace("%", "")
      if len(line) > 0:
         perc, vol = line.split(" ")
         if int(perc) >= 85:
            derrs.append("Disk volume " + str(vol) + " is " + str(perc) + "% full!")
   return(derrs)
           

def ping_cam(cam_num):
   config = read_config("conf/config-" + str(cam_num) + ".txt")
   cmd = "ping -c 1 " + config['cam_ip']
   response = os.system(cmd)
   if response == 0:
      print ("Cam is up!")
      return(1)
   else:
      print ("Cam is down!")
      return(0)

def check_stream(cam_num, stream_type):
   bad = 0
   if stream_type == 'SD': 
      cmd = "find /mnt/ams2/SD -mmin -5 |grep mp4 | grep -v proc | grep cam" + str(cam_num) + " |wc -l"
      output = subprocess.check_output(cmd, shell=True).decode("utf-8")
      output.replace("\n", "")
      if int(output) > 0:
         print ("SD cam ", str(cam_num), " is good", output)
         return(1)
      else:
         print ("SD cam ", str(cam_num), " is bad. Restart.", output)
         return(0)
   if stream_type == 'HD':
      cmd = "find /mnt/ams2/HD -mmin -5 |grep cam" + str(cam_num) + " |wc -l"
      output = subprocess.check_output(cmd, shell=True).decode("utf-8")
      output.replace("\n", "")
      if int(output) > 0:
         print ("HD cam ", str(cam_num), " is good", output)
         return(1) 
      else:
         print ("HD cam ", str(cam_num), " is bad. Restart.", output)
         return(0) 



   return(bad)
errors = []
config = read_config()
obs_name = config['obs_name']
print (obs_name)

clean_zombies()

# Check disk space 
derrs = check_disk_space()
print (derrs)

# Check Pings
bad = 0
for i in range (1,7):
   res = ping_cam(i)
   print ("Cam " + str(i) + " " + str(res))
   if res == 0: 
      errors.append("Cam " + str(i) + "did not respond to ping")
      ping_errors = 1

# Check SD Streams
stream_errors = 0
for i in range (1,7):
   res = check_stream(i, "SD")
   if res == 0:
      errors.append("Cam " + str(i) + "SD Stream not present. ")
      stream_errors = 1
# Check HD Streams
for i in range (1,7):
   res = check_stream(i, "HD")
   if res == 0:
      errors.append("Cam " + str(i) + "HD Stream not present. ")
      stream_errors = 1


msg = "Error messages for " + obs_name + "<BR>\n"
for error in derrs: 
   msg = msg + error + "<BR>\n"
   print (error)

for error in errors: 
   msg = msg + error + "<BR>\n"
   print (error)

if stream_errors == 1:
   os.system("./ffmpeg_record.py stop 1")
   time.sleep(3)
   os.system("./ffmpeg_record.py start_all")

if len(derrs) > 0 or len(errors) > 0:
   sendmail('mike.hankey@gmail.com', 'mike.hankey@gmail.com', 'AS6 Alert', msg)
