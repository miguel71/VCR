#! /usr/bin/python
import pexpect
import thread

import numpy as np
import cv2
import time
import collections

import utils

ffmpegthread = None

source_video_device_number = 0
loopback_video_device_number = 0

static_times_file_name = "cut_times.txt"

frames_since_possible_static = 0
frames_times_since_possible_static_that_arent_that_much_static = collections.deque([])

capture_started = False

current_time = "00:00:00.00"

video_ended = False
file = None

def start_video_analysis():
    global video_ended
    cap = cv2.VideoCapture(loopback_video_device_number)
    
    last_state = ""
    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        edges = cv2.Canny(frame,190,200)
       
        interpet_possible_static(frame, edges)

        state = utils.interpret_playing_state(frame)
        if state != last_state:
            print state

        if state == "STOP" or state == "REW/FORW":
            video_ended = True
            break

        last_state = state

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

def interpet_possible_static(frame, edges):
    global frames_since_possible_static
    global frames_times_since_possible_static_that_arent_that_much_static

    #remove from the list times that are older than 2 seconds
    while len(frames_times_since_possible_static_that_arent_that_much_static) > 0:
        if frames_times_since_possible_static_that_arent_that_much_static[-1]+2 < time.time():
            #print "POP " + str(frames_times_since_possible_static_that_arent_that_much_static[-1]) + " " + str(time.time())
            frames_times_since_possible_static_that_arent_that_much_static.pop()
        else:
            break
    
    """if max_difference_between_color_channels < 10 and mean_edges_value > 68:
        avg_color_gray = (avg_color[0] + avg_color[1] + avg_color[2])/3
        what_mean_edges_value_should_be_to_be_static = 0.83*avg_color_gray+40

        if what_mean_edges_value_should_be_to_be_static-10 <= mean_edges_value <= what_mean_edges_value_should_be_to_be_static+10:
            frames_since_possible_static += 1
            print time.time()
            return
        else:
            print str(what_mean_edges_value_should_be_to_be_static) + " " + str(mean_edges_value)
    """

    #mean color of the Canny image (the whiter, the more edges the video has)
    mean_edges_value = cv2.mean(edges)[0]
    avg_color = utils.calc_frame_average_color(frame)
    max_difference_between_color_channels = max(max(abs(avg_color[0] - avg_color[1]), abs(avg_color[1] - avg_color[2])), abs(avg_color[0] - avg_color[2]))

    if max_difference_between_color_channels < 10 and mean_edges_value > 80:
        frames_since_possible_static += 1
    else:
        frames_times_since_possible_static_that_arent_that_much_static.appendleft(time.time())

    #if there are many frames that probably aren't static then probably the video is no longer static
    #dont store more than 30 times in the list frames_times_since_possible_static_that_arent_that_much_static
    if len(frames_times_since_possible_static_that_arent_that_much_static) > 30:
        frames_times_since_possible_static_that_arent_that_much_static.pop()
        frames_since_possible_static = 0


def is_static():
    global frames_since_possible_static
    global frames_times_since_possible_static_that_arent_that_much_static

    return frames_since_possible_static > 5*30 and len(frames_times_since_possible_static_that_arent_that_much_static) < 10



def register_start_static_frame():
    global file, current_time
    file.write(" - " + current_time + "\n")
    file.flush()

def register_end_static_frame():
    global file, current_time
    seconds, nanoseconds = utils.time_str_to_seconds(current_time)
    seconds -= 3
    time_a_few_seconds_ago = utils.seconds_and_ns_to_time_str(seconds, nanoseconds)
    file.write(time_a_few_seconds_ago)
    file.flush()

def stop_recording(need_to_stop_ffmpeg):
    register_start_static_frame()
    if file is not None:
        file.close()
    if need_to_stop_ffmpeg:
        ffmpegthread.send("q")
        ffmpegthread.wait()
    print "Capture stopped"

def run(recording_name, recorder_dev_num, loopback_dev_num, sound_input):
    global source_video_device_number, loopback_video_device_number, ffmpegthread
    global capture_started, current_time, file, video_ended
    source_video_device_number = recorder_dev_num
    loopback_video_device_number = loopback_dev_num

    #cmd = "ffmpeg -y -f v4l2 -thread_queue_size 1024 -framerate 25 -video_size 640x480 -i /dev/video" + str(source_video_device_number) + " -f alsa -i " + str(sound_input) + " -f v4l2 /dev/video" + str(loopback_video_device_number) + " -c:v h264 -c:a aac -pix_fmt yuv420p -strict -2" + str(recording_name) + "/src.mp4"
    #cmd = "ffmpeg -y -f v4l2 -thread_queue_size 512 -framerate 25 -video_size 720x480 -i /dev/video" + str(source_video_device_number) + " -f alsa -thread_queue_size 512 -i " + str(sound_input) + " -c:v h264 -c:a aac -pix_fmt yuv420p -strict -2 " + str(recording_name) + "/src.mp4"
    cmd = "ffmpeg -y -f v4l2 -thread_queue_size 512 -framerate 25 -video_size 720x480 -i /dev/video" + str(source_video_device_number) + " -f alsa -thread_queue_size 512 -i " + str(sound_input) + " -f v4l2 /dev/video" + str(loopback_video_device_number) + " -c:v h264 -c:a aac -pix_fmt yuv420p -strict -2 " + str(recording_name) + "/src.mp4"
    print cmd

    try:
        ffmpegthread = pexpect.spawn(cmd)
        cpl = ffmpegthread.compile_pattern_list([
            pexpect.EOF,
            "frame= *\d+.*",
            "\/dev\/video*\d+: Device or resource busy"
            '(.+)'
        ])

        file = open(recording_name + "/" + static_times_file_name,"w")
        file.write("00:00:00.00")
        file.flush()

        last_frame_was_static = False

        while True:
            if video_ended:
                stop_recording(True)
                break

            i = ffmpegthread.expect_list(cpl, timeout=None)

            if i == 0: # EOF
                stop_recording(False)
                break

            elif i == 1:
                if not capture_started:
                    capture_started = True
                    thread.start_new_thread (start_video_analysis, ())
                    print "Capture started"

                frame_number = ffmpegthread.match.group(0)
                start_pos = frame_number.index('time=')+5
                end_pos = frame_number.index(' ', start_pos)
                current_time = frame_number[start_pos:end_pos]

                static = is_static()

                if static:
                    if not last_frame_was_static:
                        register_start_static_frame()
                else:
                    if last_frame_was_static:
                        register_end_static_frame()

                last_frame_was_static = static
                ffmpegthread.close
            elif i == 2:
                line = ffmpegthread.match.group(0)
                print line
            elif i == 3:
                unknown_line = ffmpegthread.match.group(0)
                print unknown_line
                pass
        
    except KeyboardInterrupt:
        stop_recording(True)