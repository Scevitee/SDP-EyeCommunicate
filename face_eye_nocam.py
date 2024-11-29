# main.py
import cv2
import sys
import dlib
import numpy as np
import imutils
import os
import sys
import pygame
import time
import pyautogui
import threading
import facegestures.pose as service
import warnings
from sklearn.exceptions import ConvergenceWarning
from imutils import face_utils
from imutils.video import VideoStream
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from collections import deque
from facegestures.gestures import *
from eyetracking.eyegestures import EyeGestures_v2
from ui.overlay import Overlay

if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"


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
        self.current_sensitivity = 0
        self.sensitivities = {
            2: {"shake_threshold": 3, "nod_threshold": 2, "eyebrow_scalar": 1.2, "ear_scalar": 0.80,
                     "gaze_time_window": 30},
            1: {"shake_threshold": 4, "nod_threshold": 3, "eyebrow_scalar": 1.35, "ear_scalar": 0.70,
                       "gaze_time_window": 50},
            0: {"shake_threshold": 5, "nod_threshold": 4, "eyebrow_scalar": 1.45, "ear_scalar": 0.60,
                    "gaze_time_window": 70}}

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
        
        self.is_eyetracking = True
        self.blink_timestamps = deque()
        self.TRIPLE_BLINK_TIME_WINDOW = 2.0  # seconds
        
        
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
                    overlay.notification_signal.emit("Blink")

            # Eyebrow raise detection on even frames
            else:
                eyebrow_raised = detect_eyebrow_raise(landmarks, shared_state)
                if eyebrow_raised and shared_state.universal_buffer_frames == 0:
                    print("Eyebrow raised!")
                    shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
                    overlay.notification_signal.emit("Eyebrow raised")
                    overlay.select_highlighted_signal.emit()  # Emit the signal to select the highlighted element

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
                overlay.change_page_signal.emit('left')
                overlay.notification_signal.emit("Page change left")
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
                
            elif look_right_detected:
                print("LOOKING RIGHT")
                overlay.change_page_signal.emit('right')
                overlay.notification_signal.emit("Page change right")
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION

            elif look_up_detected:
                print("LOOKING UP")
                overlay.zoom_in_signal.emit()
                overlay.notification_signal.emit("Zoom in")
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
                
            elif look_down_detected:
                print("LOOKING DOWN")
                overlay.zoom_out_signal.emit()
                overlay.notification_signal.emit("Zoom out")
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
            
            elif shake_detected:
                print("SHAKE DETECTED")    
                shared_state.current_sensitivity = (shared_state.current_sensitivity + 1) % 3
                shared_state.setSensitivity(shared_state.current_sensitivity)
                message = f"Sensitivity: {['Low', 'Medium', 'High'][shared_state.current_sensitivity]}"
                overlay.notification_signal.emit(message)
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION
            
            elif nod_detected:
                print("NOD DETECTED")
                overlay.toggle_pin_signal.emit()
                overlay.notification_signal.emit("Toggled pin")
                shared_state.universal_buffer_frames = shared_state.UNIVERSAL_BUFFER_DURATION

    # Decrease the universal buffer frames
    if shared_state.universal_buffer_frames > 0:
        shared_state.universal_buffer_frames -= 1



# once calibrated, the eye_gestures object will take utilize the current frame to deduce where the eyes are looking
# This will run in parallel with the gesture detections
def eye_tracking(frame, eye_gestures, screen_width, screen_height, is_eyetracking):    
    if not is_eyetracking:
        return
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gevent, _ = eye_gestures.step(
        frame,
        calibration=False,
        width=screen_width,
        height=screen_height,
        context="main"
    )

    if gevent is not None:
        gaze_point = gevent.point  # (x, y) coordinates
        # Ensure the gaze point is within screen bounds
        x = min(max(int(gaze_point[0]), 0), screen_width - 1)
        y = min(max(int(gaze_point[1]), 0), screen_height - 1)
        pyautogui.moveTo(x, y)



# def eyetracking() ..

def main():

    # Video capture
    cap = cv2.VideoCapture(0)

    framerate = 60
    radius = 400
    total_iterations = 25  # Total number of calibration points


    eye_gestures = EyeGestures_v2(radius)
    eye_gestures.setClassicalImpact(2)
    eye_gestures.setFixation(1.0)

    # Initialize Pygame
    pygame.init()
    pygame.font.init()

    # Get the display dimensions
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    # Initialize detectors and predictors
    
    # Define colors
    BACKGROUND_COLOR = (30, 30, 30)
    CALIBRATION_POINT_COLOR = (50, 49, 121)
    GAZE_POINT_COLOR = (80, 200, 120)
    TEXT_COLOR = (185, 185, 185)
    
    # Set up the screen
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Eye Tracker Calibration")

    # Load fonts with custom sizes
    font_size = 80  # Increase the font size for the pre-calibration message
    bold_font_size = 90  # Increase the font size for the countdown
    font = pygame.font.Font(None, font_size)
    bold_font = pygame.font.Font(None, bold_font_size)
    bold_font.set_bold(True)

    clock = pygame.time.Clock()

    # Optimize PyAutoGUI
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    iterator = 1
    prev_x = 0
    prev_y = 0

    # Pre-calibration message
    pre_calibration_message_line1 = "Hello! Your eye-tracking calibration is about to begin."
    pre_calibration_message_line2 = "Please try to keep your head as still as possible and focus on the number in the centers of the dots."
    countdown = 10

    # Display pre-calibration message with countdown
    for i in range(countdown, -1, -1):
        screen.fill(BACKGROUND_COLOR)
        
        # Render the first line of the pre-calibration message
        message_surface_line1 = font.render(pre_calibration_message_line1, True, TEXT_COLOR)
        message_rect_line1 = message_surface_line1.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
        screen.blit(message_surface_line1, message_rect_line1)
        
        # Render the second line of the pre-calibration message
        message_surface_line2 = font.render(pre_calibration_message_line2, True, TEXT_COLOR)
        message_rect_line2 = message_surface_line2.get_rect(center=(screen_width // 2, screen_height // 2 - 40))
        screen.blit(message_surface_line2, message_rect_line2)
        
        # Render the countdown
        countdown_surface = bold_font.render(str(i), True, TEXT_COLOR)
        countdown_rect = countdown_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
        screen.blit(countdown_surface, countdown_rect)
        
        pygame.display.flip()
        time.sleep(1)

    calibrating = True

    # Calibration Loop
    while calibrating:
        
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gevent, cevent = eye_gestures.step(
            frame,
            calibration=True,
            width=screen_width,
            height=screen_height,
            context="main"
        )

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                calibrating = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    calibrating = False

        # Calibration display
        screen.fill(BACKGROUND_COLOR)

        # Draw calibration point
        pygame.draw.circle(screen, CALIBRATION_POINT_COLOR, cevent.point, cevent.acceptance_radius)

        # Draw gaze point
        pygame.draw.circle(screen, GAZE_POINT_COLOR, gevent.point, 30)

        # Display iterator number in the center of the calibration point
        iterator_text = f"{iterator}/{total_iterations}"
        text_surface = bold_font.render(iterator_text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=cevent.point)
        screen.blit(text_surface, text_rect)

        if cevent.point[0] != prev_x or cevent.point[1] != prev_y:
            iterator += 1
            prev_x = cevent.point[0]
            prev_y = cevent.point[1]

        if iterator > total_iterations:
            calibrating = False

        pygame.display.flip()
        clock.tick(30)  # Reduce framerate to 30 FPS

    pygame.quit()

    
    
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

        # h, w, _ = frame.shape
        # Create threads
        t1 = threading.Thread(target=face_and_blink_detection, args=(frame, gray, shared_state, detector, predictor, overlay))
        t2 = threading.Thread(target=pose_estimation_and_shake_nod_detection, args=(frame, shared_state, fa, overlay))
        t3 = threading.Thread(target=eye_tracking, args=(frame, eye_gestures, screen_width, screen_height, shared_state.is_eyetracking))

        # Start threads
        t1.start()
        t2.start()
        t3.start()

        # Wait for threads to finish
        t1.join()
        t2.join()
        t3.join()


        # Process PyQt events
        app.processEvents()

        # cap.release()

    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
