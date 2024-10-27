import cv2
import dlib
import face_recognition
import numpy as np
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import time
from collections import deque
from gestures import *


cap = VideoStream(src=0).start()
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

blink_counter = 0
eyebrow_counter = 0

BLINK_QUEUE_SIZE = 5
blink_queue = deque([1] * BLINK_QUEUE_SIZE, maxlen=BLINK_QUEUE_SIZE)

buffer_frames = 0
BUFFER_DURATION = 20  

bct = 0
calibrated_ear = 0
ear_list = []
calibration_time = 2  # seconds
start_time = time.time()

calibrating = True
# Define a variable to keep track of the frames to display the message
blink_display_frames = 0
BLINK_DISPLAY_DURATION = 30  # Number of frames to show the "Blink detected" message

calibrating = True
while True:
    frame = cap.read()
    frame = imutils.resize(frame, width=800)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 20, 20)
    
    # Detect faces in the frame
    faces = detector(gray, 0)

    for face in faces:
        # Get facial landmarks
        landmarks = predictor(frame, face)
        landmarks = face_utils.shape_to_np(landmarks)
        (x, y, w, h) = face_utils.rect_to_bb(face)

        # check if in the calibration period of program
        if calibrating:
            cv2.putText(frame, "Calibrating", (x // 3, (y - (y // 2))), 2, 2, 1, 2)
            ear = calculate_ear(landmarks)
            ear_list.append(ear)

            if (time.time() - start_time) > calibration_time:
                calibrated_ear = 0.76 * np.percentile(ear_list, 5)
                print(f"Calibrated EAR: {calibrated_ear}")
                calibrating = False

        else:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)


            for (i, (x, y)) in enumerate(landmarks):
                # draw circles at the position of the facial landmarks
                cv2.circle(frame, (x, y), 1, (0, 255, 0), 1)

            # Check for specific gestures
            blink_detected, buffer_frames, blink_queue = detect_blink(landmarks, calibrated_ear, blink_queue, buffer_frames, BUFFER_DURATION)
            if blink_detected:  
                bct += 1
                # Set the blink display frames to the specified duration
                blink_display_frames = BLINK_DISPLAY_DURATION

            if detect_eyebrow_raise(landmarks):
                eyebrow_counter = 0

    # Display "Blink detected" on the frame for a few frames
    if blink_display_frames > 0:
        cv2.putText(frame, "Blink detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        blink_display_frames -= 1

    # Display the frame for debugging
    cv2.imshow('Facial Gesture Control', frame)

    # Click Q while focused on frame to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cv2.destroyAllWindows()
cap.stop()