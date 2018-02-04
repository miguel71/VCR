import os
import subprocess

dirPath = os.path.dirname(os.path.realpath(__file__))
dirName = os.path.basename(dirPath) 

final_file_name = dirName + ".mp4"

#find segment files
lst = []
for file_name in os.listdir(dirPath):
    if file_name.endswith(".mp4") and file_name.startswith("seg"):
        lst.append(file_name)
        
lst = sorted(lst)


#write their names in the concat.txt file
concat_file = file("concat.txt", "w")

for seg in lst:
    concat_file.write("file " + seg + "\n")

concat_file.close()



#concat segments
p = subprocess.Popen(['ffmpeg -f concat -i concat.txt -c copy ' + final_file_name], shell=True)
p.wait()


#remove concat.txt
os.remove("concat.txt")