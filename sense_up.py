#!/usr/bin/python3
import numpy as np
import requests
import cv2
import os
import time
import datetime
import sys
from collections import deque
import iproc


def read_config():
    config = {}
    file = open("config.txt", "r")
    for line in file:
      line = line.strip('\n')
      data = line.rsplit("=",2)
      config[data[0]] = data[1]
      #print key, value
    return(config)

def get_calibration_frames():
   config = read_config()
   print ("Sensing Up.")
   fp = open("/home/pi/fireball_camera/calnow", "w")
   r = requests.get("http://" + config['cam_ip'] + "/webs/btnSettingEx?flag=1000&paramchannel=0&paramcmd=1058&paramctrl=25&paramstep=0&paramreserved=0&")

   cap = cv2.VideoCapture("rtsp://" + config['cam_ip'] + "/av0_1&user=admin&password=admin")

   cv2.setUseOptimized(True)
   lock = open("/home/pi/fireball_camera/calibrate.txt", "w")
   time_start = time.time()
   print ("Sleep")
   time.sleep(3)
   print ("Wake")

   frames = deque(maxlen=200) 
   frame_times = deque(maxlen=200) 
   count = 0

   print ("Collecting calibration video.")
   while count < 301:
      _ , frame = cap.read()
      if _ is True:
         if count > 100:
            frame_time = time.time()
            frames.appendleft(frame)
            frame_times.appendleft(frame_time)

      if count == 300:
         print ("Saving video.")
         dql = len(frame_times) - 1
         time_diff = frame_times[1] - frame_times[dql]
         fps = 100 / time_diff
         format_time = datetime.datetime.fromtimestamp(int(frame_time)).strftime("%Y%m%d%H%M%S")
         outfile = "{}/{}.avi".format("/var/www/html/out/cal", format_time)
         if int(config['hd']) == 0:
            frame_sz = cv2.resize(frames[0], (0,0), fx=1, fy=.75)
         else:
            frame_sz = frames[0]


         writer = cv2.VideoWriter(outfile, cv2.VideoWriter_fourcc(*'MJPG'), fps, (frame_sz.shape[1], frame_sz.shape[0]), True)
         flc = 0
         while frames:
            if (flc > 30):
               img = frames.pop()
               if int(config['hd']) == 0:
                  frame_sz = cv2.resize(img, (0,0), fx=1, fy=.75)
               else:
                  frame_sz = img
               img = frame_sz

               frame_time = frame_times.pop()
               format_time = datetime.datetime.fromtimestamp(int(frame_time)).strftime("%Y%m%d%H%M%S")
               dec_sec = datetime.datetime.fromtimestamp(int(frame_time)).strftime("%f")
               format_time = format_time + dec_sec
               writer.write(img)
            flc = flc + 1
         writer.release()
      count = count + 1

   # sense camera down
   r = requests.get("http://" + config['cam_ip'] + "/webs/btnSettingEx?flag=1000&paramchannel=0&paramcmd=1058&paramctrl=50&paramstep=0&paramreserved=0&")
   cap.release()
   time.sleep(3)
   os.system("rm /home/pi/fireball_camera/calnow")
   return(outfile)

def stack_calibration_video(outfile):
   frames = deque(maxlen=200) 
   print("Stack File")
   count = 0
   show = None
   print ("/var/www/html/out/cal/" + outfile)
   cv2.namedWindow('pepe')
   cap = cv2.VideoCapture("/var/www/html/out/cal/" + outfile)
   time.sleep(2)
   count = 0
   tstamp_prev = None
   image_acc = None
   dst = None
   dst_x = None
   while count < 89:
      _ , frame = cap.read()
      print (count)
      if frame is None:
         continue
      frames.appendleft(frame)

      alpha, tstamp_prev = iproc.getAlpha(tstamp_prev)
      if count == 80:
         sframe = frame
   
      #alpha = .23
      alpha = .8
      nice_frame = frame
      #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      #frame = cv2.GaussianBlur(frame, (21, 21), 0)
      if show is None:
         show = np.empty(np.shape(frame))
      if image_acc is None:
         image_acc = np.empty(np.shape(frame))
      if dst is None:
         dst = np.empty(np.shape(frame))
      image_diff = cv2.absdiff(image_acc.astype(frame.dtype), frame,)
      hello = cv2.accumulateWeighted(frame, image_acc, alpha)
      abs_frame = cv2.convertScaleAbs(frame)
      abs_image_acc = cv2.convertScaleAbs(image_acc)
      if dst is None:
         dst = abs_image_acc
      else: 
         dst = cv2.convertScaleAbs(dst)
      dst = cv2.addWeighted(abs_frame, alpha, dst, alpha, 0)
      #nice_avg = cv2.convertScaleAbs(image_dst)
      cv2.imshow('pepe', dst)  
      cv2.waitKey(1)
      count = count + 1
   
   image_acc = np.empty(np.shape(frame))

   framex = frames[45]
   framey = frames[88]
   image_diff = cv2.absdiff(framex.astype(framey.dtype), framey,)
   print(image_diff)
   cv2.imshow("pepe",image_diff)
   cv2.waitKey(0)
   

   for i in range(1,5):
      k = i * 5 + 30
      frame = frames[i+25]
      cv2.imshow('pepe', frame)  
      cv2.waitKey(0)
      image_diff = cv2.absdiff(image_acc.astype(frame.dtype), frame,)
      cv2.imshow('pepe', image_diff)  
      cv2.waitKey(0)
      hello = cv2.accumulateWeighted(frame, image_acc, alpha)
      abs_frame = cv2.convertScaleAbs(frame)
      abs_image_acc = cv2.convertScaleAbs(image_acc)
      if dst_x is None:
         dst_x = abs_image_acc
      else: 
         dst_x = cv2.convertScaleAbs(dst_x)
      cv2.imshow('pepe', dst_x)  
      cv2.waitKey(0)


   jpg_file = outfile.replace(".avi", ".jpg")
   cv2.imwrite(jpg_file, dst)
   jpg_file_x = outfile.replace(".avi", "-x.jpg")
   cv2.imwrite(jpg_file_x, dst_x)
   jpg_file = jpg_file.replace(".jpg", "-single.jpg")
   print (jpg_file)
   sframe = cv2.convertScaleAbs(sframe)
   cv2.imwrite(jpg_file, sframe)

   #img_filt = cv2.medianBlur(cv2.imread('jpg_file',0), 5)
   #img_th = cv2.adaptiveThreshold(img_filt,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
   #contours, hierarchy = cv2.findContours(img_th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
 

cmd = sys.argv[1]

if cmd == 'sense_up':
   outfile = get_calibration_frames()
   #stack_calibration_video(outfile)
   os.system("rm /home/pi/fireball_camera/calibrate.txt")
if cmd == 'stack':
   outfile = sys.argv[2]
   stack_calibration_video(outfile)
