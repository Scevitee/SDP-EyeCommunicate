# python
import cv2
import dlib
import numpy as np
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import time
import json
import os
import keyboard  # Install with `pip install keyboard`

JSON_FILENAME = 'landmark_counters.json'

class EyebrowInfo:
    def __init__(self):
        self.initial_landmarks = None
        self.initial_left_eyb = None
        self.initial_right_eyb = None
        self.recording = False
        self.recorded_landmarks = []
        self.recorded_left_eyb = []
        self.recorded_right_eyb = []
        self.eyebrow_indices = list(range(17, 27))  # Indices for eyebrows
        self.num_landmarks = 68  # Total number of facial landmarks

        # Initialize counters
        self.counters = self.load_counters()

    def load_counters(self):
        if os.path.exists(JSON_FILENAME):
            with open(JSON_FILENAME, 'r') as f:
                return json.load(f)
        else:
            # Initialize counters for each landmark
            counters = {'left': {str(i): 0 for i in range(self.num_landmarks)},
                        'right': {str(i): 0 for i in range(self.num_landmarks)}}
            return counters

    def save_counters(self):
        with open(JSON_FILENAME, 'w') as f:
            json.dump(self.counters, f, indent=4)

    def record_initial_landmarks(self, landmarks):
        self.initial_landmarks = landmarks.copy()
        self.initial_left_eyb, self.initial_right_eyb = self.get_avg_eyb_positions(landmarks)
        print("Initial landmarks recorded.")

    def get_avg_eyb_positions(self, landmarks):
        (leStart, leEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
        (reStart, reEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]
        left_eyb = landmarks[leStart:leEnd]
        right_eyb = landmarks[reStart:reEnd]
                
        lx, ly = np.mean(left_eyb[:, 0]), np.mean(left_eyb[:, 1])
        rx, ry = np.mean(right_eyb[:, 0]), np.mean(right_eyb[:, 1])
        return (lx, ly), (rx, ry)

    def start_recording(self):
        self.recording = True
        self.recorded_landmarks = []
        self.recorded_left_eyb = []
        self.recorded_right_eyb = []
        print("Started recording landmarks.")

    def stop_recording(self):
        self.recording = False
        print("Stopped recording landmarks.")

    def add_landmarks(self, landmarks):
        self.recorded_landmarks.append(landmarks.copy())
        l_eyb, r_eyb = self.get_avg_eyb_positions(landmarks)
        self.recorded_left_eyb.append(l_eyb)
        self.recorded_right_eyb.append(r_eyb)

    def find_candidates(self):
        if (
            self.initial_landmarks is None
            or not self.recorded_landmarks
            or not self.recorded_left_eyb
            or not self.recorded_right_eyb
        ):
            print("Insufficient data to find candidates.")
            return

        num_landmarks = self.initial_landmarks.shape[0]
        left_differences = {}
        right_differences = {}

        # Calculate initial distances to left and right eyebrows
        initial_left_distances = []
        initial_right_distances = []
        for i in range(num_landmarks):
            left_dist = np.linalg.norm(self.initial_landmarks[i] - self.initial_left_eyb)
            right_dist = np.linalg.norm(self.initial_landmarks[i] - self.initial_right_eyb)
            initial_left_distances.append(left_dist)
            initial_right_distances.append(right_dist)

        # Calculate average recorded distances to left and right eyebrows
        avg_left_distances = [0.0] * num_landmarks
        avg_right_distances = [0.0] * num_landmarks
        num_frames = len(self.recorded_landmarks)

        for idx in range(num_frames):
            landmarks = self.recorded_landmarks[idx]
            l_eyb = self.recorded_left_eyb[idx]
            r_eyb = self.recorded_right_eyb[idx]
            for i in range(num_landmarks):
                left_dist = np.linalg.norm(landmarks[i] - l_eyb)
                right_dist = np.linalg.norm(landmarks[i] - r_eyb)
                avg_left_distances[i] += left_dist
                avg_right_distances[i] += right_dist

        avg_left_distances = [dist / num_frames for dist in avg_left_distances]
        avg_right_distances = [dist / num_frames for dist in avg_right_distances]

        # Calculate differences for each landmark
        for i in range(num_landmarks):
            if i not in self.eyebrow_indices:
                left_diff = abs(initial_left_distances[i] - avg_left_distances[i])
                right_diff = abs(initial_right_distances[i] - avg_right_distances[i])
                left_differences[i] = left_diff
                right_differences[i] = right_diff

        # Find landmarks with smallest differences
        sorted_left = sorted(left_differences.items(), key=lambda x: x[1])
        sorted_right = sorted(right_differences.items(), key=lambda x: x[1])

        # Update counters for top 10 landmarks
        top_n = 10
        for idx, _ in sorted_left[:top_n]:
            self.counters['left'][str(idx)] += 1
        for idx, _ in sorted_right[:top_n]:
            self.counters['right'][str(idx)] += 1

        # Save updated counters
        self.save_counters()

        # Print results
        print("\nLandmarks with the smallest change relative to the left eyebrow:")
        for idx, diff in sorted_left[:top_n]:
            print(f"Landmark {idx}: Change = {diff:.4f}")

        print("\nLandmarks with the smallest change relative to the right eyebrow:")
        for idx, diff in sorted_right[:top_n]:
            print(f"Landmark {idx}: Change = {diff:.4f}")

        print("\nUpdated Counters:")
        print("Left Eyebrow Counters (Top 10):")
        left_top_counters = sorted(self.counters['left'].items(), key=lambda x: x[1], reverse=True)[:top_n]
        for idx, count in left_top_counters:
            print(f"Landmark {idx}: Count = {count}")

        print("\nRight Eyebrow Counters (Top 10):")
        right_top_counters = sorted(self.counters['right'].items(), key=lambda x: x[1], reverse=True)[:top_n]
        for idx, count in right_top_counters:
            print(f"Landmark {idx}: Count = {count}")

# Initialize objects
eyebrow_info = EyebrowInfo()
cap = VideoStream(src=0).start()
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("../models/shape_predictor_68_face_landmarks.dat")

while True:
    frame = cap.read()
    frame = imutils.resize(frame, width=800)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 20, 20)

    faces = detector(gray, 0)
    for face in faces:
        shape = predictor(gray, face)
        face_landmarks = face_utils.shape_to_np(shape)

        # Handle key presses
        if keyboard.is_pressed('p'):
            eyebrow_info.record_initial_landmarks(face_landmarks)
            time.sleep(0.5)  # Debounce
        elif keyboard.is_pressed('o'):
            if not eyebrow_info.recording:
                eyebrow_info.start_recording()
            eyebrow_info.add_landmarks(face_landmarks)
        elif keyboard.is_pressed('q'):
            eyebrow_info.stop_recording()
            eyebrow_info.find_candidates()
            cap.stop()
            cv2.destroyAllWindows()
            exit()

        # Visualize landmarks
        for (x, y) in face_landmarks:
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

    cv2.imshow("Eyebrow Candidate Search", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.stop()
cv2.destroyAllWindows()