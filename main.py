import cv2
import dlib
import numpy as np
import imutils
import time
import keyboard
import pyautogui
import threading
import facegestures.pose as service
from dataclasses import dataclass
from imutils import face_utils
from imutils.video import VideoStream
from collections import deque
from facegestures.gestures import *
from eyetracking.eyegestures import EyeGestures_v2 


# This class holds all the data that the different processes need to access, share, and modify
# May be more appropriate to use a @dataclass object
#   -> currently not implemented as such just in case we need to add some methods to the class
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
        self.EAR_SCALAR = 0.76
        
        # Checking if centered variables
        self.IS_CENTERED_QUEUE_SIZE = 15
        self.is_centered_queue = deque([0] * self.IS_CENTERED_QUEUE_SIZE, maxlen=self.IS_CENTERED_QUEUE_SIZE)

        # Total number of frames passed
        self.frame_counter = 0

        # Eyebrow raise detection variables
        self.eyebrow_counter = 0
        self.EYEBROW_THRESHOLD = 0.475
        self.calibrated_eyebrow_distance = 0
        self.EYEBROW_SCALAR = 1.3
        self.eyebrow_list = []

        # Calibration variables
        self.calibration_time = 4  # seconds
        self.calibrating = True
        self.ear_list = []
        self.start_time = time.time()
        self.sensitivities = {"High":{"shake_threshold":2, "nod_threshold":2, "eyebrow_scalar":1.2, "ear_scalar":0.82, "gaze_time_window":30}, 
                              "Medium":{"shake_threshold":3, "nod_threshold":3, "eyebrow_scalar":1.3, "ear_scalar":0.76, "gaze_time_window":50}, 
                              "Low":{"shake_threshold":4, "nod_threshold":4, "eyebrow_scalar":1.45, "ear_scalar":0.70, "gaze_time_window":70}}

        # Shake/Nod detection variables
        self.SHAKE_THRESHOLD = 3
        self.NOD_THRESHOLD = 3
        self.GAZE_TIME_WINDOW = 50
        self.left_right_history = deque(maxlen=self.GAZE_TIME_WINDOW)
        self.up_down_history = deque(maxlen=self.GAZE_TIME_WINDOW)
        
        # Keyboard variables
        self.last_change_time = 0
        self.CHANGE_COOLDOWN_PERIOD = 5  # seconds

        # Face data
        self.dlib_faces = []

        # Lock for thread synchronization
        self.lock = threading.Lock()
        
        
    # Choose from some default sensitivity levels
    def setSensitivity(self, sensitivity):
        if sensitivity in self.sensitivities:
            self.SHAKE_THRESHOLD = self.sensitivities[sensitivity]["shake_threshold"]
            self.NOD_THRESHOLD = self.sensitivities[sensitivity]["nod_threshold"]
            self.EYEBROW_SCALAR = self.sensitivities[sensitivity]["eyebrow_scalar"]
            self.EAR_SCALAR = self.sensitivities[sensitivity]["ear_scalar"]
            self.GAZE_TIME_WINDOW = self.sensitivities[sensitivity["gaze_time_window"]]
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
           


def change_pages():
    keyboard.press_and_release('ctrl+alt+right')
    time.sleep(3)
    keyboard.press_and_release('ctrl+alt+left')


# Function for everything 'landmark related' (face detection, blink detection, eyebrow raise detection)
def face_and_blink_detection(frame, gray, shared_state, detector, predictor):
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

        if np.mean(shared_state.is_centered_queue) < 0.90 or abs(np.mean(shared_state.nod_history)) > 0.4 or abs(np.mean(shared_state.shake_history)) > 0.4:
            # Skip gesture detection if face is not centered
            continue

        # Check if in the calibration phase
        if shared_state.calibrating:
            # lock shared_state to draw the text to the frame
            with shared_state.lock:
                cv2.putText(frame, "Calibrating", (x // 3, y - (y // 2)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

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
            # Draw rectangle around the detected face
            with shared_state.lock:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
                for (x_point, y_point) in landmarks:
                    cv2.circle(frame, (x_point, y_point), 1, (0, 255, 0), 1)

            # Blink detection
            # Only perform on odd number frames
            if shared_state.frame_counter % 2:
                blink_detected, shared_state.blink_buffer_frames, shared_state.blink_history = detect_blink(
                    landmarks, shared_state.calibrated_ear, shared_state.blink_history,
                    shared_state.blink_buffer_frames, shared_state.BLINK_BUFFER_DURATION
                )
                if blink_detected:
                    shared_state.blink_counter += 1
                    shared_state.blink_display_frames = shared_state.BLINK_DISPLAY_DURATION

            # eyebrow raise detection
            else:
                eyebrow_raised = detect_eyebrow_raise(landmarks, shared_state)
                if eyebrow_raised:
                    with shared_state.lock:
                        cv2.putText(frame, "Eyebrow Raise Detected", (50 , 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        print("Eyebrow raised!")

    # Display "Blink detected" message
    if shared_state.blink_display_frames > 0:
        with shared_state.lock:
            cv2.putText(frame, "Blink detected", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        shared_state.blink_display_frames -= 1


# Func for everything 'pose related' (pose estimation, gaze direction, shake/nod detection)
def pose_estimation_and_shake_nod_detection(frame, shared_state, fa, color=(224, 255, 255)):
    # Convert dlib faces to the format required by the pose estimation model
    dense_faces = dlib_to_dense(shared_state.dlib_faces)
    for results in fa.get_landmarks(frame, dense_faces):
        # Draw pose and gaze direction
        with shared_state.lock:
            service.pose(frame, results, color)
            service.draw_gaze_direction(frame, results)

        # Get gaze directions
        gaze_horiz, gaze_vert = service.get_gaze_direction(frame, results)

        shared_state.shake_history.append(gaze_horiz)
        shared_state.nod_history.append(gaze_vert)

        # Detect shake and nod gestures
        shake_detected = service.detect_shake_nod(shared_state.shake_history, shared_state.SHAKE_THRESHOLD,
                                                  shared_state.SHAKE_NOD_TIME_WINDOW)
        nod_detected = service.detect_shake_nod(shared_state.nod_history, shared_state.NOD_THRESHOLD,
                                                shared_state.SHAKE_NOD_TIME_WINDOW)


        # TODO Add buffer period so you don't get a bunch of continuous detections
        look_left_detected = service.detect_look_left_right(shared_state.left_right_history, 'left')
        look_right_detected = service.detect_look_left_right(shared_state.left_right_history, 'right')
        
        look_up_detected = service.detect_look_up_down(shared_state.up_down_history, 'up')
        look_down_detected = service.detect_look_up_down(shared_state.up_down_history, 'down')
        
        if look_left_detected:
            print("LOOKING LEFT")
        if look_right_detected:
            print("LOOKING RIGHT")
        if look_up_detected:
            print("LOOKING UP")
        if look_down_detected:
            print("LOOKING DOWN")


        with shared_state.lock:
            service.draw_shake_nod(frame, shake_detected, nod_detected)

        # Perform action on shake detection
        current_time = time.time()
        if shake_detected and not nod_detected:
            if current_time - shared_state.last_change_time > shared_state.CHANGE_COOLDOWN_PERIOD:
                # Uncomment the following line to enable page change functionality
                # change_pages()
                shared_state.last_change_time = current_time


def main():
    
    eye_gestures = EyeGestures_v2(calibration_radius=400)
    
    # Video capture
    cap = cv2.VideoCapture(0)
    
    
    screen_width, screen_height = pyautogui.size()
    
    window_name = "Main Test"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    
    # Initialize detectors and predictors
    # dlib detector / predictor
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("facegestures/models/shape_predictor_68_face_landmarks.dat")
    # Pose estimation predictor
    # Currently implemented to utilize the dlib detector (may not be needed now that we have multithreading working)
    fa = service.DepthFacialLandmarks("facegestures/models/sparse_face.tflite")

    # Create a shared state. Consider changing to @dataclass object
    # Holds all the data that the different processes need to access, share, and modify
    shared_state = SharedState()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # frame = imutils.resize(frame, width=1200)
        
        # h, w, _ = frame.shape
        
        gevent, cevent = eye_gestures.step(
            frame,
            calibration=False,
            width=screen_width,    
            height=screen_height,  
            context="main"
        )

        if gevent is not None:
            gaze_point = gevent.point  # (x, y) coordinates

            # Display the gaze point on the frame
            cv2.circle(frame, (int(gaze_point[0]), int(gaze_point[1])), 10, (0, 0, 0), -1)
            cv2.putText(frame, f"Gaze: ({int(gaze_point[0])}, {int(gaze_point[1])})",
                        (10, screen_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # pyautogui.moveTo(int(gaze_point[0]), int(gaze_point[1]))
            
        # Create threads
        # First thread controls operations relating to face detection, blink detection/calibration, and eyebrow raise detection
        # Consider further separating these operation into their own threads
        t1 = threading.Thread(target=face_and_blink_detection, args=(frame, gray, shared_state, detector, predictor))
        t2 = threading.Thread(target=pose_estimation_and_shake_nod_detection, args=(frame, shared_state, fa))
    

        # Start threads
        t1.start()
        t2.start()

        # Wait for threads to finish
        t1.join()
        t2.join()
        
        cv2.imshow(window_name, frame)
        
        key = cv2.waitKey(1)
        if key == ord('p'):  # 'p' key to increment EYEBROW_THRESHOLD
            shared_state.setSensitivity("High")

        elif key == ord('o'):  # 'o' key to decrement EYEBROW_THRESHOLD
            shared_state.setSensitivity("Medium")
            
        elif key == ord('i'):  # 'i' key to decrement EYEBROW_THRESHOLD
            shared_state.setSensitivity("Low")
            
        elif key == ord('0'):
            shared_state.tweakSensitivity('EYEBROW_SCALAR', 0.001)

        elif key == ord('9'):
            shared_state.tweakSensitivity('EYEBROW_SCALAR', 0.001, decrease=True)

        elif key == ord('q'):
            break
        # Display the frame

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()



# Test function for the eyebrow raise candidates
#   Get norm of left eyebrow and right eyebrow
#   On keypress store the positions of landmarks
#   Tilt head up -> hit separate key to start recording all the new landmarks
#       # return candidate landmarks based on how little they changed

