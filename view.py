#!/usr/bin/python3 
import pytesseract
from pathlib import Path
import glob
import collections
from collections import deque
from PIL import Image, ImageChops
from queue import Queue
import multiprocessing
import datetime
import cv2
import numpy as np
import iproc 
import time
import ephem
import sys
import os
MORPH_KERNEL       = np.ones((10, 10), np.uint8)

def day_or_night(file):

   year = file[0:4]
   month = file[4:6]
   day = file[6:8]
   hour = file[8:10]
   min = file[10:12]
   sec = file[12:14]
   date_str = year + "/" + month + "/" + day + " " + hour + ":" + min
   print("File:", file)
   print(year,month,day,hour,min,sec)
   config = read_config()
   obs = ephem.Observer()
   obs.pressure = 0
   obs.horizon = '-0:34'
   obs.lat = config['cam_lat']
   obs.lon = config['cam_lon']
   #cur_date = time.strftime("%Y/%m/%d %H:%M")
   cur_date = datetime.datetime.strptime(date_str, "%Y/%m/%d %H:%M")
   obs.date = cur_date
   print ("FILE DATE: ", cur_date)
   sun = ephem.Sun()
   sun.compute(obs)
   if sun.alt > -10:
      status = "day"
   else:
      status = "night"

   #print (obs.lat, obs.lon, obs.date)
   #print ("Sun Alt: %s, Sun AZ: %s" % (sun.alt, sun.az))
   (sun_alt, x,y) = str(sun.alt).split(":")
   (sun_az, x,y) = str(sun.az).split(":")
   print ("Sun Alt: %s" % (sun_alt))
   if int(sun_alt) < -10:
      status = "dark";
   if int(sun_alt) >- 10 and int(sun_alt) < 5:
      if int(sun_az) > 0 and int(sun_az) < 180:
         status = "dawn"
      else:
         status = "dusk"
   if int(sun_alt) >= 5:
      status = "day";

   return(status)

def read_config():
    config = {}
    file = open("config.txt", "r")
    for line in file:
      line = line.strip('\n')
      data = line.rsplit("=",2)
      config[data[0]] = data[1]
      #print key, value

    config['az_left'] = int(config['cam_heading']) - (int(config['cam_fov_x'])/2)
    config['az_right'] = int(config['cam_heading']) + (int(config['cam_fov_x'])/2)
    if (config['az_right'] > 360):
       config['az_right'] = config['az_right'] - 360
    if (config['az_left'] > 360):
       config['az_left'] = config['az_left'] - 360
    if (config['az_left'] < 0):
       config['az_left'] = config['az_left'] + 360
    config['el_bottom'] = int(config['cam_alt']) - (int(config['cam_fov_y'])/2)
    config['el_top'] = int(config['cam_alt']) + (int(config['cam_fov_y'])/2)
    return(config)

def analyze(file):
    a = 0
    b = 0
    bright_pixel_count = 0
    bright_pixel_total = 0
    elapsed_frames = 0
    cons_motion = 0
    straight_line = 100
    straight = 'N'
    motion = 0
    motion_off = 0
    frame_data = {}
    data_file = file.replace(".avi", ".txt");
    summary_file = data_file.replace(".txt", "-summary.txt")
    object_file = data_file.replace(".txt", "-objects.jpg")
    fp = open(data_file, "r")
    sfp = open(summary_file, "w")
    event_start_frame = 0
    event_end_frame = 0
    sum_color = 0
    cons_motion = 1 
    max_cons_motion = 0
    cons_motion_events = 0
    last_motion = 0
    mid_pix_count = 0
    for line in fp:
       (frame,contours,area,perimeter,convex,x,y,w,h,middle_pixel,n) = line.split("|")
       if (middle_pixel== ""):
          middle_pixel= 0
       if frame != 'frame':
          if contours != "":
             motion = motion + 1
             motion_off = 0
             if last_motion > 0:
                cons_motion = cons_motion + 1
             if cons_motion > max_cons_motion:
                max_cons_motion = cons_motion
          if motion < 5  and contours == "":
             motion = 0
             last_motion = 0
             cons_motion = 0
          if motion == 5 and event_start_frame == 0:
             event_start_frame = int(frame) 
          if motion >= 1 and contours == "":
             motion_off = motion_off + 1
          if motion > 5 and motion_off > 5 and event_end_frame == 0:
             event_end_frame = int(frame) - 5 
          if int(middle_pixel) > 0:
             sum_color = sum_color + int(middle_pixel)
             mid_pix_count = mid_pix_count + 1
             if int(middle_pixel) >= 190:
                print ("Bright Pixel Count/Mid Pix Total", bright_pixel_count, middle_pixel)
                bright_pixel_count = bright_pixel_count + 1
                bright_pixel_total = bright_pixel_total + int(middle_pixel)


          out = str(frame)+","+str(contours)+","+str(area)+","+str(perimeter)+","+str(convex)+","+str(x) + "," + str(y) + "," + str(w) + "," + str(h) + "," + str(middle_pixel) + "," + str(n) + ",\n"
          frame_data.update({int(frame) : {'x': x, 'y': y}})
          sfp.write(out)
          cons_motion = motion
          print(out)
          if (event_start_frame != 0 and event_end_frame == 0 and middle_pixel != ""):
             #print ("COLOR:", color)
             last_frame_motion = motion
             last_frame_cnts = contours 
    out = "Event Start Frame : " + str(event_start_frame) + "\n"
    sfp.write(out)
    print (out)
    out = "Event End Frame : " + str(event_end_frame) + "\n"
    sfp.write(out)
    print (out)
    if (bright_pixel_count > 0):
       out = "Bright Frames: " + str(bright_pixel_count) + "\n"
       sfp.write(out)
       print (out)
       out = "Bright Frame Avg: " + str(bright_pixel_total/bright_pixel_count) + "\n"
       sfp.write(out)
       print (out)
    sfp.write(out)
    print (out)

    key_frame1 = int(event_start_frame)
    key_frame2 = int(event_start_frame + ((int(event_end_frame - event_start_frame) / 2)))
    key_frame3 = int(event_end_frame - 3)
    ofr = collections.OrderedDict(sorted(frame_data.items()))

    out = "Key Frames: " + str(key_frame1) + "," + str(key_frame2) + "," + str(key_frame3) + "\n"
    sfp.write(out)
    print (out)
    elapsed_frames = key_frame3 - key_frame1
    if cons_motion > 0 and mid_pix_count > 0:
       avg_center_pixel = int(sum_color) / mid_pix_count
    else:
       avg_center_pixel = 0
    out = "Sum Color/Frames: " + str(sum_color) + "/" + str(mid_pix_count) + "\n"
    sfp.write(out)
    print (out)
    out = "Consectutive Motion Frames: " + str(max_cons_motion) + "\n"
    sfp.write(out)
    print (out)
    if max_cons_motion > 10 and event_end_frame > 0 and 'x' in frame_data[key_frame3] and 'x' in frame_data[key_frame2] and 'x' in frame_data[key_frame1]:
       if ( frame_data[key_frame1]['x'] != '' and frame_data[key_frame2]['x'] != '' and frame_data[key_frame3]['x'] != '' ):
          x1 = int(frame_data[key_frame1]['x'])
          y1 = int(frame_data[key_frame1]['y'])
          #print("X2: ", frame_data[key_frame2]['x'])
          x2 = int(frame_data[key_frame2]['x'])
          y2 = int(frame_data[key_frame2]['y'])
          x3 = int(frame_data[key_frame3]['x'])
          y3 = int(frame_data[key_frame3]['y'])

          if x2 - x1 != 0:
             a = (y2 - y1) / (x2 - x1)
          if x3 - x1 != 0:
             b = (y3 - y1) / (x3 - x1)
          straight_line = a - b
          if (straight_line < 1):
             straight = "Y" 
    else: 
       out = "Not enough consecutive motion."
       sfp.write(out)
       print (out)
       
    meteor = "N"
    if (straight_line < 1 and avg_center_pixel > 425 or (bright_pixel_count > 10 )):
       meteor = "Y"
    sfp.write("Elapsed Frames:\t" + str(elapsed_frames)+ "\n")
    print("Elapsed Frames:\t" + str(elapsed_frames)+ "\n")
    sfp.write("Straight Line:\t" + str(straight) + "," + str(straight_line)+"\n")
    print("Straight Line:\t" + str(straight) + "," + str(straight_line)+"\n")
    sfp.write("Average Center Pixel Color:\t" + str(avg_center_pixel) + "\n")
    print("Average Center Pixel Color:\t" + str(avg_center_pixel) + "\n")
    sfp.write("Likely Meteor:\t"+ str(meteor)+"\n")
    print("Likely Meteor:\t"+ str(meteor)+"\n")
    if meteor == "N":
       false_file= file.replace("out/", "out/false/")
       false_data_file= data_file.replace("out/", "out/false/")
       false_summary_file= summary_file.replace("out/", "out/false/")
       false_object_file = object_file.replace("out/", "out/false/")
       cmd = "mv " + file + " " + false_file 
       os.system(cmd)
       cmd = "mv " + data_file + " " + false_data_file
       os.system(cmd)
       cmd = "mv " + summary_file + " " + false_summary_file
       os.system(cmd)
       cmd = "mv " + object_file + " " + false_object_file
       os.system(cmd)
    else:  
       maybe_file= file.replace("out/", "out/maybe/")
       maybe_data_file= data_file.replace("out/", "out/maybe/")
       maybe_summary_file= summary_file.replace("out/", "out/maybe/")
       cmd = "mv " + file + " " + maybe_file 
       maybe_object_file = object_file.replace("out/", "out/maybe/")
       os.system(cmd)
       cmd = "mv " + data_file + " " + maybe_data_file
       os.system(cmd)
       cmd = "mv " + summary_file + " " + maybe_summary_file
       os.system(cmd)
       cmd = "mv " + object_file + " " + maybe_object_file
       os.system(cmd)
  
def view(file, show):
    jpg = file
    data_file = file
    jpg = jpg.replace(".avi", ".jpg");
    jpg = jpg.replace("out", "jpgs");
    data_file = data_file.replace(".avi", ".txt");
    object_file = data_file.replace(".txt", "-objects.jpg")

    cap = cv2.VideoCapture(file)
    final_cv_image = None
    time.sleep(2)

    tstamp_prev = None
    image_acc = None
    last_frame = None
    nice_image_acc = None
    final_image = None
    cur_image = None
    if show == 1:
       cv2.namedWindow('pepe')
    count = 0
    frames = deque(maxlen=256)
    out_jpg = np.zeros((500,500,3))
    out_jpg_final = np.zeros((500,500,3))
    oy = 0
    ox = 0
    max_h = 0
    fp = open(data_file, "w")
    fp.write("frame|contours|area|perimeter|convex|x|y|w|h|color|\n")
    mid_pix_total = 0
    mid_pix_count = 0
    while True:
        frame_file = jpg.replace(".jpg", "-" + str(count) + ".jpg");
        _ , frame = cap.read()
        #cv2.imwrite(frame_file, frame)
        if frame is None:
           if count == 0:
               print ("bad file!")
               return()
           #print (jpg)
           #cv2.imwrite(jpg, final_cv_image)
           if max_h <= 500:
              out_jpg_final = out_jpg[0:max_h,0:500]
           else: 
              out_jpg_final = out_jpg[0:500,0:500]
           if max_h > 0:
              cv2.imwrite(object_file, out_jpg_final)
           else: 
              cv2.imwrite(object_file, out_jpg)
           return()
           #exit()

#        frames.appendleft(frame)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        alpha, tstamp_prev = iproc.getAlpha(tstamp_prev)
        #print ("ALPHA: ", alpha)
        nice_frame = frame
        #frame = cv2.resize(frame, (0,0), fx=0.8, fy=0.8)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (21, 21), 0)
        if last_frame is None:
            last_frame = frame 
        if image_acc is None:
            image_acc = np.empty(np.shape(frame))
        image_diff = cv2.absdiff(image_acc.astype(frame.dtype), frame,)
        hello = cv2.accumulateWeighted(frame, image_acc, alpha)
        _, threshold = cv2.threshold(image_diff, 30, 255, cv2.THRESH_BINARY)
        thresh= cv2.dilate(threshold, None , iterations=2)
        (_, cnts, xx) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        data = str(count) + "|" 
        if len(cnts) > 0:

            image_diff = cv2.absdiff(last_frame.astype(frame.dtype), frame,)
            _, threshold = cv2.threshold(image_diff, 30, 255, cv2.THRESH_BINARY)
            thresh= cv2.dilate(threshold, None , iterations=2)
            (_, alt_cnts, xx) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(alt_cnts) != 0:
               cnts = alt_cnts

            area = cv2.contourArea(cnts[0])
            perim = cv2.arcLength(cnts[0], True)
            #print ("Perim:", perim)
            #for cnt in cnts:
            x,y,w,h = cv2.boundingRect(cnts[0])
               

            #ellipse = cv2.fitEllipse(cnts[0])
            #print ("Ellipse:", len(ellipse), ellipse)
            #if len(ellipse) == 5:
            #   cv2.ellipse(frame,ellipse,(0,255,0),2)

            # crop out
            x2 = x+w
            y2 = y+h
            mx = int(x + (w/2))
            my = int(y + (h/2))
 
            #print ("XY:", x,x2,y,y2)

            gray_frame = cv2.cvtColor(nice_frame, cv2.COLOR_BGR2GRAY)
            middle_pixel = gray_frame[my,mx]
            middle_sum = np.sum(middle_pixel)
            #print("MID PIX:", middle_pixel, middle_sum)
            mid_pix_total = mid_pix_total + middle_pixel
            mid_pix_count = mid_pix_count + 1
            cv2.circle(nice_frame,(mx,my),5,(255,0,0))
            crop_frame = nice_frame[y:y2,x:x2]
            cy = (y + y2) / 2
            cx = (x + x2) / 2
            text = (pytesseract.image_to_string(Image.fromarray(crop_frame)))
            print (text)
            if h > max_h and h < 300:
               max_h = h
               print ("MAX Height Hit", max_h)

            if (ox + w) < 500 and (oy + h) < 500 and len(text) == 0:
               print ("OY,OY+H,OX,OX+W,color,cnts: ", oy, oy+h, ox, ox+w, middle_pixel, len(cnts))
               try: 
                  out_jpg[oy:oy+h,ox:ox+w] = crop_frame
               except:
                  print("crop too big for summary!")
               if show == 1:
                  cv2.imshow('pepe', cv2.convertScaleAbs(out_jpg))
                  cv2.waitKey(1) 
               ox = ox +w
            else: 
               print("Crop to big for summary pic!", oy,oy+h,ox,ox+w,h,w)
               time.sleep(5)
            if (ox + w ) >= 500 and (w < 400):
               oy += max_h
               ox = 0  


            avg_color_per_row = np.average(crop_frame, axis=0)
            avg_color = np.average(avg_color_per_row, axis=0)
            #print ("AVG COLOR: " , avg_color, np.sum(avg_color))
            tjpg = jpg
            tjpg = tjpg.replace(".jpg", "-" + str(count) + ".jpg")
           # print ("TJPG", tjpg)
            cv2.imwrite(tjpg, crop_frame)


            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,255),1)

            poly = cv2.approxPolyDP(cnts[0], 0.02*perim, True)

            #print ("Poly: ", poly)
            #print ("Convex?: ", cv2.isContourConvex(cnts[0]))
            convex = cv2.isContourConvex(cnts[0])
            #data = "frame|contours|area|perimeter|poly|convex|x|y|w|h|color|\n" 
            data = data + str(len(cnts)) + "|" + str(area) + "|" + str(perim) + "|"
            #data = data + str(poly) + "|"
            data = data + str(convex) + "|"
            data = data + str(x) + "|"
            data = data + str(y) + "|"
            data = data + str(w) + "|"
            data = data + str(h) + "|"
            data = data + str(middle_pixel) + "|"
        else:
            data = data + "|||||||||"
        fp.write(data + "\n")
    
        last_frame = frame 



        #nice_avg = cv2.convertScaleAbs(nice_image_acc)

        #print (cnts)


        #if cur_image is None:
        #    cur_image = Image.fromarray(frame)

            #temp = cv2.convertScaleAbs(nice_image_acc)
            #nice_image_acc_pil = Image.fromarray(temp)
            #cur_image = ImageChops.lighter(cur_image, nice_image_acc_pil)

        #final_cv_image = np.array(cur_image)
        #cv2.imshow('pepe', final_cv_image)
        #if count % 1 == 0:
        #    cv2.imshow('pepe', frame)
        count = count + 1
        #print (count)
        #cv2.waitKey(1)

try: 
   file = sys.argv[1]
   batch = 0
except:
   files = glob.glob("/var/www/html/out/*.avi") 
   batch = 1

if batch == 0:
   status = day_or_night(file)
   print ("This video was taken during: ", status)
   view("/var/www/html/out/" + file, 1)
   analyze("/var/www/html/out/" + file)
else:
   for file in files:
      file = file.replace("/var/www/html/out/", "")
      print (file)  
      view("/var/www/html/out/" + file, 0)
      analyze("/var/www/html/out/" + file)


