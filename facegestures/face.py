import cv2
import dlib
import face_recognition
import numpy as np
import imutils
import time
import keyboard
import pose as service
from imutils import face_utils
from imutils.video import VideoStream
from collections import deque
from gestures import *

def change_pages():
    keyboard.press_and_release('ctrl+alt+right')
    time.sleep(3)
    keyboard.press_and_release('ctrl+alt+left')


   
def main(color=(224, 255, 255)):

    # Video capture
    cap = cv2.VideoCapture(0)
    
    # dlib's face detector / landmark predictor
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

    # pose estimator's face detector / landmark predictor
    fd = service.UltraLightFaceDetection("models/RFB-320.tflite", conf_threshold=0.95)
    fa = service.DepthFacialLandmarks("models/sparse_face.tflite")

    # Shake/Nod Vars
    SHAKE_THRESHOLD = 3
    NOD_THRESHOLD = 3
    SHAKE_NOD_TIME_WINDOW = 20   #frames
    shake_history = deque(maxlen=SHAKE_NOD_TIME_WINDOW)
    nod_history = deque(maxlen=SHAKE_NOD_TIME_WINDOW)
    
    # Eyebrow Vars
    eyebrow_counter = 0
    
    # Blink vars
    blink_counter = 0  # Mostly for print statement debugging
    BLINK_QUEUE_SIZE = 5
    blink_history = deque([1] * BLINK_QUEUE_SIZE, maxlen=BLINK_QUEUE_SIZE)
    BLINK_DISPLAY_DURATION = 30   # Frames to keep blink message on screen
    blink_display_frames = 0  # How many frames has the blink message been displayed so far
    BLINK_BUFFER_DURATION = 20  # How long to wait until we can check for another blink
    blink_buffer_frames = 0  # Track how long program has been waiting so far
    
    # Calibration vars
    calibration_time = 2  # seconds
    calibrating = True
        # Blink calibration
    ear_list = []
    calibrated_ear = 0
    
    # Keyboard vars
    # Most of this stuff is placeholder variables for random stuff like
    # having a function change the tabs on my screen 
    last_change_time = 0  
    CHANGE_COOLDOWN_PERIOD = 5  # In seconds (don't want pages changing a bunch rapidly)
    
    dlib_faces = []
    
    # Detection Loop
    start_time = time.time()
    while True:
        
        # init the frame
        ret, frame = cap.read()
        if not ret:
            break
        
        # create base frame and a gray version (for dlib)
        frame = imutils.resize(frame, width=800)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # gray = cv2.bilateralFilter(gray, 7, 20, 20)   # Needs testing to see if it actually does anything
        
        # Get all the dlib_faces in the frame and loop through them
        temp_faces = detector(gray, 0)
        if len(temp_faces) != 0:
            dlib_faces = temp_faces
         
        for face in dlib_faces:
            # Get the dlib facial landmarks
            landmarks = predictor(frame, face)
            landmarks = face_utils.shape_to_np(landmarks)
            (x, y, w, h) = face_utils.rect_to_bb(face)
            
            
            #check if in the calibration period of the program
            if calibrating:
                cv2.putText(frame, "Calibrating", (x // 3, (y - (y // 2))), 2, 2, 1, 2)
                ear = calculate_ear(landmarks)
                ear_list.append(ear)

                if (time.time() - start_time) > calibration_time:
                    calibrated_ear = 0.76 * np.percentile(ear_list, 5)
                    print(f"Calibrated EAR: {calibrated_ear}")
                    calibrating = False  
            else:
                # if not calibrating, draw all the dlib stuff / 
                # enable program to check for blinks
                
                # Draw rectangle around the detected face(s)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)

                # draw circles at the position of the facial landmarks
                for (i, (x, y)) in enumerate(landmarks):
                    cv2.circle(frame, (x, y), 1, (0, 255, 0), 1)

                # INSERT DLIB-SPECIFIC FACIAL GESTURE DETECTIONS BELOW
                
                blink_detected, blink_buffer_frames, blink_history = detect_blink(landmarks, calibrated_ear, blink_history, blink_buffer_frames, BLINK_BUFFER_DURATION)
                if blink_detected:  
                    blink_counter += 1
                    # Set the blink display frames to the specified duration
                    blink_display_frames = BLINK_DISPLAY_DURATION

                # if detect_eyebrow_raise(landmarks):
                #     eyebrow_counter = 0
                    
        # Draw dlib related stuff to the frame
         
        # Display "Blink detected" on the frame for a few frames
        if blink_display_frames > 0:
            cv2.putText(frame, "Blink detected", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            blink_display_frames -= 1
    
    
        # Get the pose_estimation faces and loop through them
        # boxes, score = fd.inference(frame)
        
        # Currently I am taking the face recognitions from dlib and converting them into a format that 
        # the headpose code agrees with. Some precision is sacrificed, but this improves performance, 
        # as it eliminates the need to detect the faces twice        
        dense_faces = dlib_to_dense(dlib_faces)
        
        for results in fa.get_landmarks(frame, dense_faces):
            service.pose(frame, results, color)
            # Draw functions are built into the functions for pose-estimation
            # No need to draw them after this detection loop
            service.draw_gaze_direction(frame, results)
            
            gaze_horiz, gaze_vert = service.get_gaze_direction(frame, results)
            shake_history.append(gaze_horiz)
            nod_history.append(gaze_vert)
            
            shake_detected = service.detect_shake_nod(shake_history, SHAKE_THRESHOLD, SHAKE_NOD_TIME_WINDOW)
            nod_detected = service.detect_shake_nod(nod_history, NOD_THRESHOLD, SHAKE_NOD_TIME_WINDOW)
            
            service.draw_shake_nod(frame, shake_detected, nod_detected)
        
            current_time = time.time()
            if shake_detected and not nod_detected:
                # Only invoke change_pages if cooldown period has passed
                if current_time - last_change_time > CHANGE_COOLDOWN_PERIOD:
                        # change_pages()
                        last_change_time = current_time     
        
        cv2.imshow("demo", frame)
        if cv2.waitKey(1) == ord('q'):
            break


if __name__ == '__main__':
    main()
    