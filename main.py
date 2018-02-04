import os.path
import sys
import subprocess
import os
import shutil

import numpy as np
import cv2

import utils
import recorder

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#config
#
recorder_device_number = 0
loopback_device_number = 1
extra_loopback_device_number = 2

sound_input = "hw:2,0"

#Checks if a device exists
def device_exists(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True

def wait_for_cassette(wait_for_state):
    cap = cv2.VideoCapture(recorder_device_number)
    last_state = ""
    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()

        edges = cv2.Canny(frame,190,200)
       
        state = utils.interpret_playing_state(frame, edges)
        if state != last_state:
            print state
        
        if state == wait_for_state:
            break
        last_state = state

    cap.release()

#Check if source video device exists
if not device_exists("/dev/video" + str(recorder_device_number)):
    print "source device /dev/video" + str(recorder_device_number) + " doesn't exist"
    sys.exit()

#Check if loopback video device exists. If not creates one with v4l2loopback
loopback_device_exists = device_exists("/dev/video" + str(loopback_device_number))
extra_loopback_device_exists = extra_loopback_device_number != -1 and device_exists("/dev/video" + str(extra_loopback_device_number))

#If one only one loopback device exists, but there should be two, unload v4l2loopback
if extra_loopback_device_number != -1 and (not loopback_device_exists and extra_loopback_device_exists) or (loopback_device_exists and not extra_loopback_device_exists):
    print "unloading v4l2loopback"
    p = subprocess.Popen(['sudo modprobe v4l2loopback -r'], shell=True)
    p.wait()

loopback_device_exists = device_exists("/dev/video" + str(loopback_device_number))
extra_loopback_device_exists = extra_loopback_device_number != -1 and device_exists("/dev/video" + str(extra_loopback_device_number))

#Create loopback and extra loopback devices, if necessary
if not loopback_device_exists and not extra_loopback_device_exists:
    print "loopback device /dev/video" + str(loopback_device_number) + " and extra loopback device /dev/video" + str(extra_loopback_device_number) + " don't exist. Creating"
    p = subprocess.Popen(['sudo modprobe v4l2loopback video_nr=' + str(loopback_device_number) + "," + str(extra_loopback_device_number)], shell=True)
    p.wait()

#Create only the loopback device, since extra loopback is not wanted
elif not loopback_device_exists and extra_loopback_device_number == -1:
    print "loopback device /dev/video" + str(loopback_device_number) + " doesn't exist. Creating"
    p = subprocess.Popen(['sudo modprobe v4l2loopback video_nr=' + str(loopback_device_number)], shell=True)
    p.wait()


while True:
    while True:
        print bcolors.OKGREEN + "Type QUIT to quit"
        recording_name = raw_input("What is the name of the cassette? " + bcolors.ENDC)
        if recording_name.strip().lower() == "quit":
            break

        if os.path.exists(recording_name):
            print "there is already a folder or file with that name"
        else:
            os.makedirs(recording_name)
            break
    
    if recording_name.strip().lower() == "quit":
        break

    
    print "Please insert the cassette"
    
    #TODO fix this
    #wait for the cassette to be inserted
    #wait_for_cassette("PLAYING")
    #wait for the cassette to rewind completely
    #wait_for_cassette("PLAY")

    raw_input("Rewind it and press enter")
    recorder.run(recording_name, recorder_device_number, loopback_device_number, sound_input)

    
    shutil.copy2('cutter.py', recording_name + "/cutter.py")
    shutil.copy2('concat.py', recording_name + "/concat.py")