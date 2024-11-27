import cv2
import sys
import dlib
import numpy as np
import imutils
import sys
import time
import pyautogui
import threading
import facegestures.pose as service
from dataclasses import dataclass
from imutils import face_utils
from imutils.video import VideoStream
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from collections import deque
from facegestures.gestures import *
from eyetracking.eyegestures import EyeGestures_v2
from ui.overlay import Overlay

"""
    This is a copy of our main.py file from presentation 2, but without the webcam display.
    I have tried to add as many comments as possible to explain how things are working here. 
"""

# This class holds all the data that the different threads need to access, share, and modify
class SharedState:
    def __init__(self):
        # Blink detection variables
        self.blink_counter = 0
        self.BLINK_QUEUE_SIZE = 5
        self.blink_history = deque([1] * self.BLINK_QUEUE_SIZE, maxlen=self.BLINK_QUEUE_SIZE)
        self.BLINK_DISPLAY_DURATION = 30
        self.blink_display_frames = 0
        self.BLINK_BUFFER_DURATION = 20
        self.blink_buffer_frames = 0
        self.calibrated_ear = 0
        self.EAR_SCALAR = 0.70   # larger value == easier to detect blinks
        
        # Checking if centered variables
        self.IS_CENTERED_QUEUE_SIZE = 15
        self.is_centered_queue = deque([0] * self.IS_CENTERED_QUEUE_SIZE, maxlen=self.IS_CENTERED_QUEUE_SIZE)

        # Total number of frames passed
        self.frame_counter = 0

        # Eyebrow raise detection variables
        self.eyebrow_counter = 0
        self.EYEBROW_THRESHOLD = 0.475     # Deprecated / no longer in use
        self.calibrated_eyebrow_distance = 0
        self.EYEBROW_SCALAR = 1.35   # Larger val == eyebrows have to raised higher in order to detect
        self.eyebrow_list = []

        # Calibration variables
        self.calibration_time = 3  # seconds
        self.calibrating = True
        self.ear_list = []
        self.start_time = time.time()
        
        # Dictionary of dictionaries used to change how easy / hard it is to trigger different gestures
        # Higher sensitivity == 'more sensitive', i.e., easier to trigger detection
        # Should be modified based on testing
        self.sensitivities = {"High":{"shake_threshold":3, "nod_threshold":2, "eyebrow_scalar":1.2, "ear_scalar":0.80, "gaze_time_window":30}, 
                              "Medium":{"shake_threshold":4, "nod_threshold":3, "eyebrow_scalar":1.35, "ear_scalar":0.70, "gaze_time_window":50}, 
                              "Low":{"shake_threshold":5, "nod_threshold":4, "eyebrow_scalar":1.45, "ear_scalar":0.60, "gaze_time_window":70}}

        # Shake/Nod detection variables
        self.SHAKE_THRESHOLD = 4  # Number of changes from left->right to count as a shake
        self.NOD_THRESHOLD = 4   # Number of changes from up->down to count as a nod
        self.GAZE_TIME_WINDOW = 50   # Number of frames to check for shake/nod. Also used to check for gaze left/right and gaze up/down
        self.left_right_history = deque([0] * self.GAZE_TIME_WINDOW, maxlen=self.GAZE_TIME_WINDOW)   
        self.up_down_history = deque([0] * self.GAZE_TIME_WINDOW, maxlen=self.GAZE_TIME_WINDOW)
        
        # Keyboard variables
        self.last_change_time = 0
        self.CHANGE_COOLDOWN_PERIOD = 5  # seconds

        # Face data
        self.dlib_faces = []

        # Lock for thread synchronization
        self.lock = threading.Lock()
        
        # Universal buffer duration and counter
        self.UNIVERSAL_BUFFER_DURATION = 50
        self.universal_buffer_frames = 0
        
        
    # Choose from some default sensitivity levels
    def setSensitivity(self, sensitivity):
        if sensitivity in self.sensitivities:
            self.SHAKE_THRESHOLD = self.sensitivities[sensitivity]["shake_threshold"]
            self.NOD_THRESHOLD = self.sensitivities[sensitivity]["nod_threshold"]
            self.EYEBROW_SCALAR = self.sensitivities[sensitivity]["eyebrow_scalar"]
            self.EAR_SCALAR = self.sensitivities[sensitivity]["ear_scalar"]
            self.GAZE_TIME_WINDOW = self.sensitivities[sensitivity]["gaze_time_window"]
            # print(f"Sensitivity changed to {sensitivity}!")
            # print(f"Shake Threshold: {self.SHAKE_THRESHOLD}")
            # print(f"Nod Threshold: {self.NOD_THRESHOLD}")
            # print(f"Eyebrow Scalar: {self.EYEBROW_SCALAR}")
            # print(f"Ear Scalar: {self.EAR_SCALAR}")
            # print()
        else:
            print(f"Invalid sensitivity level: {sensitivity}")
            
    # Manually adjust a variable by a specified amount
    def tweakSensitivity(self, attribute, amount=0.001, decrease=False):
        current_value = getattr(self, attribute)
        # Check if the current value is a number (for incrementing)
        if isinstance(current_value, (int, float)):
            # Increment the variable by the specified amount (bound between 0-1)
            if not decrease:
                setattr(self, attribute, round(current_value + amount, 4))
            else:
                setattr(self, attribute, round(current_value - amount, 4))
                
            print(f"{attribute}: {getattr(self, attribute)}")
        else:
            print(f"Error: {attribute} is not a number and cannot be incremented.")
           

# Function for everything 'landmark related' (face detection, blink detection, eyebrow raise detection)
def face_and_blink_detection(frame, gray, shared_state, detector, predictor, overlay):
    
    # print("MADE IT TO FACE AND BLINK")
    # Necessary measurements to determine if face is centered
    frame_center_x, frame_center_y = frame.shape[1] // 2, frame.shape[0] // 2
    center_margin_x, center_margin_y = frame.shape[1] * 0.2, frame.shape[0] * 0.2
    shared_state.frame_counter += 1
    
    # Detect faces using dlib
    temp_faces = detector(gray, 0)
    # If the detector finds a face THIS frame, update it. Otherwise, keep the face found in the previous frame
    if len(temp_faces) != 0:
        shared_state.dlib_faces = temp_faces

    # Loop through each face found
    for face in shared_state.dlib_faces:
        # Get facial landmarks
        landmarks = predictor(gray, face)
        # landmarks = predictor(frame, face)
        landmarks = face_utils.shape_to_np(landmarks)
        (x, y, w, h) = face_utils.rect_to_bb(face)

        face_center_x, face_center_y = x + w // 2, y + h // 2
        is_centered = (abs(face_center_x - frame_center_x) < center_margin_x) and \
                      (abs(face_center_y - frame_center_y) < center_margin_y)

        shared_state.is_centered_queue.append(is_centered)

        if np.mean(shared_state.is_centered_queue) < 0.90 or abs(np.mean(shared_state.up_down_history)) > 0.4 or abs(np.mean(shared_state.left_right_history)) > 0.4:
            # Skip gesture detection if face is not centered
            continue

        # Check if in the calibration phase
        if shared_state.calibrating:
            # Store Eye Aspect Ratio (EAR) values for calibration
            ear = calculate_ear(landmarks)
            shared_state.ear_list.append(ear)
            
            # Store eyebrow distances for calibration
            eyebrow_dist = calculate_eyebrow_distance(landmarks)
            shared_state.eyebrow_list.append(eyebrow_dist)

            if (time.time() - shared_state.start_time) > shared_state.calibration_time:
                shared_state.calibrated_ear = shared_state.EAR_SCALAR * np.percentile(shared_state.ear_list, 5)
                shared_state.calibrated_eyebrow_distance = np.percentile(shared_state.eyebrow_list, 5)
                print(f"Calibrated EAR: {shared_state.calibrated_ear}")
                print(f"Calibrated Eyebrow Distance: {shared_state.calibrated_eyebrow_distance}")
                shared_state.calibrating = False
                shared_state.ear_list = []
                shared_state.eyebrow_list = []
        else:
            # Blink detection
            # Only perform on odd number frames
            """
            This is called 'frame-skipping'. This prevents us from having to do a bunch of sequential detections
            Blink will be detected on odd frames, eyebrows on even, this doesn't have a noticeable impact on accuracy
            but is a great performance optimization
            """
            if shared_state.frame_counter % 2:
                blink_detected, shared_state.blink_buffer_frames, shared_state.blink_history = detect_blink(
                    landmarks, shared_state.calibrated_ear, shared_state.blink_history,
                    shared_state.blink_buffer_frames, shared_state.BLINK_BUFFER_DURATION
                )
                if blink_detected and shared_state.universal_buffer_frames == 0:
                    shared_state.blink_counter += 1
                    shared_state.blink_display_frames = shared_state.BLINK_DISPLAY_DURATION
                    shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION

            # Eyebrow raise detection on even frames
            else:
                eyebrow_raised = detect_eyebrow_raise(landmarks, shared_state)
                if eyebrow_raised and shared_state.universal_buffer_frames == 0:
                    print("Eyebrow raised!")
                    pyautogui.press('enter')
                    shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION

    # Decrease the blink display frame counter
    if shared_state.blink_display_frames > 0:
        shared_state.blink_display_frames -= 1

    # Decrease the universal buffer frames
    if shared_state.universal_buffer_frames > 0:
        shared_state.universal_buffer_frames -= 1


# Function for everything 'pose related' (pose estimation, gaze direction, shake/nod detection)
def pose_estimation_and_shake_nod_detection(frame, shared_state, fa, overlay, color=(224, 255, 255)):
    # Convert dlib faces to the format required by the pose estimation model
    # print("MADE IT TO POSE")
    dense_faces = dlib_to_dense(shared_state.dlib_faces)
    for results in fa.get_landmarks(frame, dense_faces):
        # Get gaze directions
        gaze_horiz, gaze_vert = service.get_gaze_direction(frame, results)

        shared_state.left_right_history.append(gaze_horiz)
        shared_state.up_down_history.append(gaze_vert)

        # Detect shake and nod gestures
        shake_detected = service.detect_shake_nod(shared_state.left_right_history, shared_state.SHAKE_THRESHOLD,
                                                  shared_state.GAZE_TIME_WINDOW)
        nod_detected = service.detect_shake_nod(shared_state.up_down_history, shared_state.NOD_THRESHOLD,
                                                shared_state.GAZE_TIME_WINDOW)

        # Detect if holding left/right or up/down gaze
        look_left_detected = service.detect_look_left_right(shared_state.left_right_history, 'left')
        look_right_detected = service.detect_look_left_right(shared_state.left_right_history, 'right')
        
        look_up_detected = service.detect_look_up_down(shared_state.up_down_history, 'up')
        look_down_detected = service.detect_look_up_down(shared_state.up_down_history, 'down')
        
        # Only act if universal buffer is zero
        if shared_state.universal_buffer_frames == 0:
            if look_left_detected:
                print("LOOKING LEFT")
                overlay.change_page_directional('left')
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
                
            elif look_right_detected:
                print("LOOKING RIGHT")
                overlay.change_page_directional('right')
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION

            elif look_up_detected:
                print("LOOKING UP")
                overlay.zoom_in()
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
                
            elif look_down_detected:
                print("LOOKING DOWN")
                overlay.zoom_out()
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
            
            elif shake_detected:
                print("SHAKE DETECTED")                
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
            
            elif nod_detected:
                print("NOD DETECTED")
                overlay.toggle_pin()                
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION

    # Decrease the universal buffer frames
    if shared_state.universal_buffer_frames > 0:
        shared_state.universal_buffer_frames -= 1


def main():
    eye_gestures = EyeGestures_v2(calibration_radius=400)

    # Video capture
    cap = cv2.VideoCapture(0)

    screen_width, screen_height = pyautogui.size()

    # Initialize detectors and predictors
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("facegestures/models/shape_predictor_68_face_landmarks.dat")
    fa = service.DepthFacialLandmarks("facegestures/models/sparse_face.tflite")

    # Create a shared state
    shared_state = SharedState()

    # Initialize the QApplication and Overlay
    app = QApplication(sys.argv)
    app.setStyle('QtCurve')
    overlay = Overlay()
    overlay.show()
    overlay.destroyed.connect(app.quit)  # Ensures the program exits when the overlay is closed

    # Function to process frames in a separate thread
    # print("entering main loop")
    while True:
        # print("looping")
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        h, w, _ = frame.shape

        gevent, cevent = eye_gestures.step(
            frame,
            calibration=False,
            width=w,
            height=h,
            context="main"
        )

        if gevent is not None:
            gaze_point = gevent.point  # (x, y) coordinates

            # Display the gaze point on the frame
            cv2.circle(frame, (int(gaze_point[0]), int(gaze_point[1])), 10, (0, 0, 0), -1)
            cv2.putText(frame, f"Gaze: ({int(gaze_point[0])}, {int(gaze_point[1])})",
                        (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # pyautogui.moveTo(int(gaze_point[0]), int(gaze_point[1]))

        # Create threads
        t1 = threading.Thread(target=face_and_blink_detection, args=(frame, gray, shared_state, detector, predictor, overlay))
        t2 = threading.Thread(target=pose_estimation_and_shake_nod_detection, args=(frame, shared_state, fa, overlay))

        # Start threads
        t1.start()
        t2.start()

        # Wait for threads to finish
        t1.join()
        t2.join()


        # Process PyQt events
        app.processEvents()

        # cap.release()

    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
