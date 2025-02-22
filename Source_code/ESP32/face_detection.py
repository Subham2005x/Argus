import pandas as pd
import cv2
import urllib.request
import numpy as np
import os
from datetime import datetime
import face_recognition

# Create attendance directory if it doesn't exist
attendance_dir = os.path.join(os.getcwd(), 'attendance')
if not os.path.exists(attendance_dir):
    os.makedirs(attendance_dir)

attendance_file = os.path.join(attendance_dir, 'Attendance.csv')

# Check if attendance file exists
if os.path.exists(attendance_file):
    print("Attendance file exists, removing it...")
    os.remove(attendance_file)

# Create new attendance file
df = pd.DataFrame(list())
df.to_csv(attendance_file)

# Create image_folder directory if it doesn't exist
image_dir = os.path.join(os.getcwd(), 'image_folder')
if not os.path.exists(image_dir):
    os.makedirs(image_dir)
    print(f"Created image folder at: {image_dir}")

# Update path to use the local image_folder
path = image_dir
url = 'http://192.168.30.169/cam-hi.jpg'
##'''cam.bmp / cam-lo.jpg /cam-hi.jpg / cam.mjpeg '''

# Add error handling for loading images
images = []
classNames = []
try:
    myList = os.listdir(path)
    print(f"Found {len(myList)} images in folder")
    for cl in myList:
        img_path = os.path.join(path, cl)
        curImg = cv2.imread(img_path)
        if curImg is not None:
            images.append(curImg)
            classNames.append(os.path.splitext(cl)[0])
        else:
            print(f"Failed to load image: {cl}")
    print(f"Loaded {len(classNames)} images successfully: {classNames}")
except Exception as e:
    print(f"Error accessing image folder: {e}")
    exit(1)

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

def markAttendance(name):
    with open(attendance_file, 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
            if name not in nameList:
                now = datetime.now()
                dtString = now.strftime('%H:%M:%S')
                f.writelines(f'\n{name},{dtString}')

encodeListKnown = findEncodings(images)
print('Encoding Complete')

#cap = cv2.VideoCapture(0)

while True:
    #success, img = cap.read()
    img_resp=urllib.request.urlopen(url)
    imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
    img=cv2.imdecode(imgnp,-1)
# img = captureScreen()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
# print(faceDis)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
# print(name)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            markAttendance(name)

    cv2.imshow('Webcam', img)
    key=cv2.waitKey(5)
    if key==ord('q'):
        break
cv2.destroyAllWindows()
cv2.imread