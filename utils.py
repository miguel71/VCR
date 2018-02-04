import math
import cv2
import numpy as np

def aproximate_contours(cnts):
    aproximated_contours = []

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        aproximated_contours.append(approx)
        
        #aproximated_contours.append(aproximated_contour)
    return aproximated_contours

def remove_video_outline_contour(cnts, width, height):
    new_cnts = []
    for c in cnts:
        area = cv2.contourArea(c)
        if round(area/(width * height), 1) != 0.9:
            new_cnts.append(c)
    return new_cnts
        
def calc_frame_average_color(frame):
    avg_color_per_row = np.average(frame, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    return avg_color

def interpret_playing_state(frame):
    height, width = frame.shape[:2]
    avg_color = calc_frame_average_color(frame)

    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    ret,threshold = cv2.threshold(blurred,127,255,cv2.THRESH_BINARY)

    (cnts, _) = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]

    a = remove_video_outline_contour(cnts, width, height)
    aproximated_contours = aproximate_contours(a)

    #cv2.drawContours(frame, cnts, 1, (0,150,255), 3)
    #print aproximated_contours
    #print str(avg_color) + " " + str(len(aproximated_contours))
    if avg_color[0] > 70 and avg_color[1] < 6 and avg_color[2] < 6:
        if len(aproximated_contours) == 1:
            center = get_shape_center_point(aproximated_contours[0])
            relative_pos_of_square = (float(center[0])/width, float(center[1])/height)
            
            #if shape is on the upper left corner
            if 0.12 < relative_pos_of_square[0] < 0.16 and 0.27 < relative_pos_of_square[1] < 0.28:
                #if it's a square
                if len(aproximated_contours[0]) == 4:
                        #cv2.imwrite('x.png',frame)
                        #print cnts
                        #print aproximated_contours
                        return "STOP"
                #if it's a triangle
                if len(aproximated_contours[0]) == 3:
                        return "PLAY"
        elif len(aproximated_contours) == 2:
            center0 = get_shape_center_point(aproximated_contours[0])
            center1 = get_shape_center_point(aproximated_contours[1])
            relative_pos_of_shape0 = (float(center0[0])/width, float(center0[1])/height)
            relative_pos_of_shape1 = (float(center1[0])/width, float(center1[1])/height)
            #if shape is on the upper left corner
            if 0.15 < relative_pos_of_shape0[0] < 0.16 and 0.26 < relative_pos_of_shape0[1] < 0.29 and 0.14 < relative_pos_of_shape1[0] < 0.15 and 0.26 < relative_pos_of_shape1[1] < 0.29:
                #if it's a two triangles
                if (len(aproximated_contours[0]) == 3 and len(aproximated_contours[1]) >= 3) or (len(aproximated_contours[0]) >= 3 and len(aproximated_contours[1]) == 3):
                    return "REW/FORW"

        return "BLUE"

    return "PLAYING"

def get_shape_center_point(shape):
    x = 0
    y = 0
    for point in shape:
        x += point[0][0]
        y += point[0][1]
    
    return [x/len(shape), y/len(shape)]

def time_str_to_seconds(time_str):
    seconds_str, nano_str = time_str.split('.')
    h, m, s = seconds_str.split(':')
    return (int(h) * 3600 + int(m) * 60 + int(s), int(nano_str))

def seconds_and_ns_to_time_str(seconds, nanoseconds):
    h = seconds / 3600
    remainder = seconds % 3600
    m = remainder/60
    remainder = seconds % 3600 % 60
    s = remainder
    return add_zeros_to_make_two(str(h)) + ":" + add_zeros_to_make_two(str(m)) + ":" + add_zeros_to_make_two(str(s)) + "." + add_zeros_to_make_two(str(nanoseconds))


def add_zeros_to_make_two(str):
    if len(str) == 1:
        return "0" + str
    elif len(str) == 0:
        return "00"

    return str