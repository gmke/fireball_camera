#!/usr/bin/python3
from collections import defaultdict
#from random import *
import random
import glob
import subprocess
import cgi
import cgitb
import os
import requests
video_dir = "/mnt/ams2/SD/"
from pathlib import Path

#cgi.enable()
print ("Content-type: text/html\n\n")

def get_mac(cam_ip):
   # get the mac address
   mac = ""
   url = "http://" + str(cam_ip) + "/cgi-bin/sysparam_cgi?user=admin&pwd=admin"
   #url = "http://" + str(cam_ip) + "/cgi-bin/sysparam_cgi?user=admin&pwd=xrp23q"
   r = requests.get(url)
   lines = r.text.split("\n")
   for line in lines:
      #print(line)
      if "MACAddress" in line:
         line = line.replace("\t", "");
         line = line.replace("<MACAddress>", "");
         line = line.replace("</MACAddress>", "");
         mac = line.replace("-", ":")
   return(mac)

def ping_cam(ip):
   cmd = "ping -c 1 " + ip + " > /dev/null"
   
   #output = subprocess.check_output(cmd, shell=True).decode("utf-8")
   response = os.system(cmd)
   if response == 0:
      os.system("/home/ams/fireball_camera/get_latest.py 6 " + ip + "&")
      el = ip.split(".")
      im = el[-1] 
      print("<img src='/out/latest-" + im+ ".jpg' width=640 height=360><HR>")
      print ("Cam found on: " + ip + "<BR>")
      mac = get_mac(ip)
      return(1, mac)
   else:
      print ("Cam NOT found on: " + ip + "<BR>")
      return(0, "")
  

def scan_network():
   cams_found = 0  
   mac = ""
   ip_range = "192.168.76."
   for i in range(70,85):
      ip = ip_range + str(i)
      status, mac = ping_cam(ip)
      if status == 1: 
         print("<input type=text name=found_" + str(cams_found) + " value=" + str(mac) + "><BR>")
         print("<select name=assign_" + str(cams_found) + ">")
         print("<option value=1>Assign as Cam 1 (North)</option>")
         print("<option value=2>Assign as Cam 2 (North East)</option>")
         print("<option value=3>Assign as Cam 3 (South East)</option>")
         print("<option value=4>Assign as Cam 4 (South West)</option>")
         print("<option value=5>Assign as Cam 5 (North West)</option>")
         print("<option value=6>Assign as Cam 6 (Up)</option>")
         print("</select>")
         print ("<hr>")
         if cams_found == 5:
            print ("all cams found")
            break
         cams_found = cams_found + 1



def assign_ips_to_macs():
   form = cgi.FieldStorage()
   act = form.getvalue('act')
   dhcp_data = {}
   dhcp_data[form.getvalue('assign_0')] = form.getvalue('found_0')
   dhcp_data[form.getvalue('assign_1')] = form.getvalue('found_1')
   dhcp_data[form.getvalue('assign_2')] = form.getvalue('found_2')
   dhcp_data[form.getvalue('assign_3')] = form.getvalue('found_3')
   dhcp_data[form.getvalue('assign_4')] = form.getvalue('found_4')
   dhcp_data[form.getvalue('assign_5')] = form.getvalue('found_5')

#http://192.168.1.14/pycgi/setup-dhcp.py?act=assign_ips_to_macs&found_0=&assign_0=1&found_1=&assign_1=3&found_2=&assign_2=5&found_3=&assign_3=4&found_4=&assign_4=2&found_5=&assign_5=6&save=Reassign+DHCP+Camera+Assignments

   dhcp_text = {}
   print ("<HR><pre>yo")
   print (dhcp_data)
   for pos in dhcp_data:
      if pos is not None:
         mac = dhcp_data[pos]
         if mac != None:
            id = pos
            dhcp_text[id] = "host cam" + str(pos) + "{\n"
            dhcp_text[id] = dhcp_text[id] + "   hardware ethernet " + mac + ";\n"
            dhcp_text[id] = dhcp_text[id] + "   fixed-address 192.168.76.7" + str(pos) + ";\n}\n"

   print ("YO<PRE>")
   #print (dhcp_text)
   print (dhcp_text['1'])
   print (dhcp_text['2'])
   print (dhcp_text['3'])
   print (dhcp_text['4'])
   print (dhcp_text['5'])
   print (dhcp_text['6'])
   print ("YO")
   print ("</PRE>")
#host cam6 {
#  hardware ethernet 00:b9:7d:7f:17:ac;
#  fixed-address 192.168.176.76;  
#}


def main():
   form = cgi.FieldStorage()
   act = form.getvalue('act')
   #act = "scan_network"
   if act == None:
      act = "scan_network"
   print ("<h1>Camera DNS Setup</h1>")
   print ("Functions <UL>")
   print ("<li><a href=setup-dhcp.py?act=view_dhcp_conf>View DHCP config file</a></li>")
   print ("<li><a href=setup-dhcp.py?act=scan_network>Scan network for cameras</a></li>")


   if act == 'assign_ips_to_macs':
      assign_ips_to_macs()

   if act == 'view_dhcp_conf':
      view_dhcp_conf()
   if act == 'scan_network':
      print ("<form>")
      print ("<input type=hidden name=act value=assign_ips_to_macs>")
      scan_network()
      print ("<input type=submit name=save value=\"Reassign DHCP Camera Assignments\">") 
      print ("</form>")
   
def view_dhcp_conf():
   cmd = "cat /etc/dhcp/dhcpd.conf"
   output = subprocess.check_output(cmd, shell=True).decode("utf-8")
   print ("<PRE>")
   print(output)
   print ("</PRE>")

main()
