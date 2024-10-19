import argparse
import cv2
import pose_service as service
import numpy as np
import time
from collections import deque


def main(color=(224, 255, 255)):

     SHAKE_THRESHOLD = 3
     NOD_THRESHOLD = 3
     TIME_WINDOW = 20
     shake_history = deque(maxlen=TIME_WINDOW)
     nod_history = deque(maxlen=TIME_WINDOW)

     fd = service.UltraLightFaceDetection("models/RFB-320.tflite", conf_threshold=0.95)
     fa = service.DepthFacialLandmarks("models/sparse_face.tflite")
     cap = cv2.VideoCapture(0)
     
     start_time = time.time()
     while True:
          ret, frame = cap.read()
          if not ret:
               break

          boxes, score = fd.inference(frame)
          # print(boxes)
          
          feed = frame.copy()
          
          for results in fa.get_landmarks(feed, boxes):
               service.pose(frame, results, color)
               service.draw_gaze_direction(frame, results)
               
               gaze_horiz, gaze_vert = service.get_gaze_direction(frame, results)
               shake_history.append(gaze_horiz)
               nod_history.append(gaze_vert)
               
               shake_detected = service.detect_shake_nod(shake_history, SHAKE_THRESHOLD, TIME_WINDOW)
               nod_detected = service.detect_shake_nod(nod_history, NOD_THRESHOLD, TIME_WINDOW)
               
               service.draw_shake_nod(frame, shake_detected, nod_detected)
          
  
          cv2.imshow("demo", frame)
          if cv2.waitKey(1) == ord('q'):
               break
          
          
if __name__ == '__main__':
    main()