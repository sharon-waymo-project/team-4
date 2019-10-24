import numpy as np
import cv2

names = ['car.mp4', 'basic_animation_latest.mp4'];
window_titles = ['first', 'second']


cap = [cv2.VideoCapture(i) for i in names]

frames = [None] * len(names);
gray = [None] * len(names);
ret = [None] * len(names);

while True:

    for i,c in enumerate(cap):
        if c is not None:
            ret[i], frames[i] = c.read();


    for i,j in enumerate(frames):
        if j is not None:
            frames[i] = cv2.resize(frames[i],(640,360))

    for i,f in enumerate(frames):
        if ret[i] is True:
            #gray[i] = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            cv2.imshow(window_titles[i], f);

    if cv2.waitKey(1) & 0xFF == ord('q'):
       break


for c in cap:
    if c is not None:
        c.release();

cv2.destroyAllWindows()