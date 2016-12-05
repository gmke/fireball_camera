import cv2
import numpy as np

jpg_file = "calibresult.png"
star_file = "stars-out.jpg"
image = cv2.imread(jpg_file)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#gray = cv2.GaussianBlur(gray, (1,1), 1)
#gray = cv2.medianBlur(gray, 1)
#cv2.imshow("Image", gray)
#cv2.waitKey(0)
limit_low = 60 
limit_up =  245
last_x = 0
last_y = 0
stars_found = 0
stars = []
data = None
for y in range(gray.shape[0] - 100):
   for x in range(gray.shape[1]):
      pixel = gray.item(y,x)
      if pixel > limit_low and pixel < limit_up: 
         x1 = x - 4 
         x2 = x + 5 
         y1 = y - 4 
         y2 = y + 5 
         x3 = x - 1 
         x4 = x + 1  
         y3 = y - 1 
         y4 = y + 1 
         crop_frame = gray[y1:y2,x1:x2]
         small_crop_frame = gray[y3:y4,x3:x4]

         avg_pix = np.average(crop_frame)
         avg_pix_s = np.average(small_crop_frame)
         #print ("SAVG:", avg_pix_s)
         diff = avg_pix_s - avg_pix

         x_y_diff = abs((last_x + last_y) - (x + y))
         if crop_frame.shape[0] > 0 and crop_frame.shape[1] > 0 and diff > 5 and (x_y_diff > 4):
            #print ("X,Y,AVG,SAVG,DIFF:", x,y,pixel,avg_pix, avg_pix_s)

            #edges = cv2.Canny(crop_frame,80,200)

#            print (crop_frame.argmax(axis=0))
            o,p = np.unravel_index(crop_frame.argmax(), crop_frame.shape)
            off_x = p -4
            off_y = o -4 
            cor_x = x + off_x
            cor_y = y + off_y
            cor_val = gray[cor_y,cor_x] 
            #print("Max Pixel in crop:", o,p, crop_frame[o,p])
            #print("MAX PIXEL GRAY XY:", x,y,gray[y,x])
            #print("Corrected gray xy ", off_x, off_y, cor_x, cor_y, cor_val )
            #print(crop_frame[o,p])
            #print (crop_frame)
            x1 = cor_x - 4 
            x2 = cor_x + 5 
            y1 = cor_y - 4 
            y2 = cor_y + 5 
            x3 = cor_x - 1 
            x4 = cor_x + 1  
            y3 = cor_y - 1 
            y4 = cor_y + 1 

            new_crop_frame = gray[y1:y2,x1:x2]
            new_crop_frame_sm = gray[y3:y4,x3:x4]

            avg_pix = np.average(new_crop_frame)
            avg_pix_s = np.average(new_crop_frame_sm)

            #print (new_crop_frame)
             
            #print (edges)
            #cv2.circle(crop_frame, (bx, by), 5, (255,0,0), 1, 1)

 
            
            #cv2.imshow("Image", new_crop_frame)
            #cv2.waitKey(0)
            last_x = x
            last_y = y
            #add pixel here
            pix_dif = avg_pix_s - avg_pix;
            stars.append((cor_x,cor_y,avg_pix,avg_pix_s,pix_dif)) 
            stars_found = stars_found + 1
      else:
         pass

dtype = [('x', int), ('y', int), ('avg_pix', float), ('avg_pix_s', float), ('pix_dif', float)]
star_arry = np.array(stars, dtype=dtype)
np.sort(star_arry, order='pix_dif')
 
print ("Stars Found: ", stars_found)
for star_x, star_y, pix_val, pix_val_sm,pix_dif in np.sort(star_arry,order='pix_dif')[::-1]:
      print (star_x, star_y)
      cv2.circle(gray, (star_x, star_y), 10, (255,0,0), 1, 1)

cv2.imshow("Image", gray)
cv2.waitKey(0)

cv2.imwrite(star_file, gray)

exit()


params = cv2.SimpleBlobDetector_Params()

params.minThreshold = 200 
params.maxThreshold = 255 

params.filterByArea = True
params.minArea = 3 
#params.maxArea = 100

params.filterByConvexity = False 
#params.minConvexity = .87
#params.maxConvexity = 1
#params.minCircularity= .1

detector = cv2.SimpleBlobDetector_create(params)

keypoints = detector.detect(gray)

im_with_points = cv2.drawKeypoints(gray, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
cv2.imshow("Image", im_with_points)
cv2.waitKey(0)


exit()
thresh = 150 
maxValue=255

th, dst = cv2.threshold(gray, thresh, maxValue, cv2.THRESH_BINARY)

#(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(gray)
#cv2.circle(gray, maxLoc, 5, (255, 0, 0), 2)
#view_mask = cv2.convertScaleAbs(gray)
#exit()

cv2.imshow("Image", dst)
cv2.waitKey(0)
#(contours, hierarchy, x) = cv2.findContours(img_filt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#print (len(contours))

#for c in contours:
#   print (c)
   #cv2.drawContours(img_filt, [c], -1, (0, 255,0), 2)
   #cv2.imshow("Image", img_filt)
   #cv2.waitKey(0)
