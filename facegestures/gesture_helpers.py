# Helper functions for gesture detection
import  numpy as np
import  cv2
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import dlib


"""
     HEADPOSE ESTIMATION
"""

def get_headpose_points(face_landmarks):
     nose = tuple(face_landmarks[30])
     chin = tuple(face_landmarks[8])
     left_eye = tuple(face_landmarks[36])
     right_eye = tuple(face_landmarks[45])
     left_mouth = tuple(face_landmarks[48])
     right_mouth = tuple(face_landmarks[54])
     
     headpose_points = np.array([
          nose,
          chin,
          left_eye,
          right_eye,
          left_mouth,
          right_mouth
     ], dtype="double")

     return headpose_points


def get_gaze_direction(rotation_vector):
    # Convert rotation vector to Euler angles
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    euler_angles = cv2.RQDecomp3x3(rotation_matrix)[0]
    
    # Get yaw (left/right) and pitch (up/down) angles
    yaw = euler_angles[1]
    pitch = euler_angles[0]
    
    horiz = 0
    if yaw < -10:
        horiz = -1  # Looking Left
    elif yaw > 10:
        horiz = 1   # Looking Right

    vert = 0
    if pitch < -.1: # Looking Down
        vert = -1
    elif pitch > .1: # Looking Up
        vert = 1
    
    return horiz, vert

def detect_head_shake_nod(gaze_history, shake_threshold, time_window):
    if len(gaze_history) < time_window:
        return False
    
    direction_changes = sum(1 for i in range(1, len(gaze_history)) if gaze_history[i] != gaze_history[i-1] and gaze_history[i] != 0)
    
    return direction_changes >= shake_threshold



# -------------------------------------------------


"""
     BLINK DETECTION
"""

# Calculate average of LeftEye-EAR and RightEye-EAR
def calculate_ear(face_landmarks):
    def eye_aspect_ratio(eye):
        # Compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])

        # Compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = np.linalg.norm(eye[0] - eye[3])

        # Compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    # Get the facial landmarks for the left and right eye
    left_eye = face_landmarks[lStart:lEnd]
    right_eye = face_landmarks[rStart:rEnd]

    # Calculate the eye aspect ratio for both eyes
    left_ear = eye_aspect_ratio(left_eye)
    right_ear = eye_aspect_ratio(right_eye)

    # Average the eye aspect ratio together for both eyes
    avg_ear = (left_ear + right_ear) / 2.0
    return avg_ear


def detect_blink(face_landmarks, eye_ar_threshold, blink_queue, buffer_frames, BUFFER_DURATION):
    ear = calculate_ear(face_landmarks)
    blink_queue.append(ear)
    
    # If we're in the buffer period, decrement the counter and don't detect blinks
    if buffer_frames > 0:
        buffer_frames -= 1
        return False, buffer_frames, blink_queue

    # Check if the average EAR is below the threshold, indicating a blink
    if np.mean(blink_queue) < eye_ar_threshold:
        print(f"Blink detected! EAR: {np.mean(blink_queue)}")
        # Reset the buffer period to prevent detecting multiple blinks in quick succession
        buffer_frames = BUFFER_DURATION
        return True, buffer_frames, blink_queue

    # No blink detected, return current state
    return False, buffer_frames, blink_queue

# -------------------------------------------------

"""
     EYEBROW RAISE DETECTION
"""

def detect_eyebrow_raise(face_landmarks, threshold=0.426, eyeb_raise_consec_frames=3):
    global eyebrow_counter

    # Get the positions of the eyebrows and eyes
    (leStart, leEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
    (reStart, reEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    (nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]

    left_eyebrow = face_landmarks[leStart:leEnd]
    right_eyebrow = face_landmarks[reStart:reEnd]
    left_eye = face_landmarks[lStart:lEnd]
    right_eye = face_landmarks[rStart:rEnd]
    nose = face_landmarks[nStart:nEnd]

    left_br_low = np.linalg.norm(left_eyebrow[2] - left_eye[3])
    left_br_hi = np.linalg.norm(left_eyebrow[2] - nose[3])
    left_br_ratio = left_br_low / left_br_hi

    right_br_low = np.linalg.norm(right_eyebrow[2] - right_eye[0])
    right_br_hi = np.linalg.norm(right_eyebrow[2] - nose[3])
    right_br_ratio = right_br_low / right_br_hi

    brow_ratio = np.mean([left_br_ratio, right_br_ratio])

    if brow_ratio > threshold:
        eyebrow_counter += 1
    else:
        if eyebrow_counter >= eyeb_raise_consec_frames:
            return True