import subprocess

def cut_segment(start_time, end_time, srcName, dstName):
    p = subprocess.Popen(['ffmpeg -y -ss ' + start_time + ' -i ' + srcName + ' -vcodec copy -acodec copy -to ' + end_time + ' ' + dstName], shell=True)
    p.wait()
    return p.returncode

srcName = "src.mp4"
with open('cut_times.txt') as f:
    lines = f.readlines()
    i = 0

    success = True

    for line in lines:
        if len(line) < 25:
            print "Incomplete line"
        else:
            start_time, end_time = line.split(" - ")
            end_time = end_time.replace('\n', '')

            dstName = "seg" + str(i) + ".mp4"
            error_code = cut_segment(start_time, end_time, srcName, dstName)
            if not error_code == 0:
                print "Error"
                success = False
                break
        i += 1