# Helper functions for gesture detection
import  numpy as np
import  cv2
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import dlib
import mediapipe as mp


"""
     HEADPOSE ESTIMATION
"""


DLIB_TO_MEDIAPIPE_LANDMARKS = {
    0: 10,    # Jawline start - closest approximation
    1: 109,   # Jawline
    2: 67,    # Jawline
    3: 103,   # Jawline
    4: 54,    # Jawline
    5: 21,    # Jawline
    6: 162,   # Jawline
    7: 127,   # Jawline
    8: 152,   # Chin tip
    9: 234,   # Jawline
    10: 93,   # Jawline
    11: 132,  # Jawline
    12: 58,   # Jawline
    13: 172,  # Jawline
    14: 136,  # Jawline
    15: 150,  # Jawline
    16: 149,  # Jawline end
    17: 33,   # Left eyebrow start
    18: 160,  # Left eyebrow
    19: 158,  # Left eyebrow
    20: 157,  # Left eyebrow
    21: 159,  # Left eyebrow end
    22: 263,  # Right eyebrow start
    23: 387,  # Right eyebrow
    24: 385,  # Right eyebrow
    25: 384,  # Right eyebrow
    26: 386,  # Right eyebrow end
    27: 1,    # Nose bridge top
    28: 2,    # Nose bridge
    29: 98,   # Nose bridge
    30: 1,    # Nose tip
    31: 248,  # Left nostril
    32: 456,  # Left nostril edge
    33: 168,  # Nose bottom
    34: 412,  # Right nostril
    35: 352,  # Right nostril edge
    36: 33,   # Left eye corner (outer)
    37: 133,  # Left eye top (outer)
    38: 155,  # Left eye top (inner)
    39: 154,  # Left eye corner (inner)
    40: 153,  # Left eye bottom (inner)
    41: 144,  # Left eye bottom (outer)
    42: 263,  # Right eye corner (outer)
    43: 362,  # Right eye top (outer)
    44: 387,  # Right eye top (inner)
    45: 386,  # Right eye corner (inner)
    46: 385,  # Right eye bottom (inner)
    47: 373,  # Right eye bottom (outer)
    48: 61,   # Mouth left corner
    49: 185,  # Upper lip left
    50: 40,   # Upper lip middle
    51: 0,    # Upper lip center
    52: 267,  # Upper lip right
    53: 269,  # Upper lip right
    54: 291,  # Mouth right corner
    55: 375,  # Lower lip right
    56: 321,  # Lower lip middle
    57: 17,   # Lower lip center
    58: 314,  # Lower lip left
    59: 402,  # Lower lip left
    60: 61,   # Mouth inner left corner
    61: 146,  # Mouth inner top left
    62: 91,   # Mouth inner top center
    63: 181,  # Mouth inner top right
    64: 84,   # Mouth inner right corner
    65: 191,  # Mouth inner bottom right
    66: 95,   # Mouth inner bottom center
    67: 88    # Mouth inner bottom left
}

DLIB_HEADPOSE_POINTS = (30, 8, 36, 45, 48, 54)

def get_headpose_points(face_landmarks):
     temp = [face_landmarks[i] for i in DLIB_HEADPOSE_POINTS]

     headpose_points_2d = np.array(temp, dtype="double")

     return headpose_points_2d

def get_mp_model_points(mp_landmarks, size): 
    h, w, _ = size
    temp = []
    
    # I want the nose z-coordinate to be very far away 
    nose = mp_landmarks.landmark[DLIB_TO_MEDIAPIPE_LANDMARKS[DLIB_HEADPOSE_POINTS[0]]]
    temp.append(tuple((nose.x * w, nose.y * h, abs(nose.z * 3000))))
        
    for i in DLIB_HEADPOSE_POINTS[1:]:
        lm = DLIB_TO_MEDIAPIPE_LANDMARKS[i]
        landmark = mp_landmarks.landmark[lm]
        p = tuple((landmark.x  * w, landmark.y * h, landmark.z ))
        temp.append(p)
    
    mp_model_points = np.array(temp, dtype="double")
    return mp_model_points


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


"""  
    Used to detect either a head shake or a head nod (they both require the same logic)
    Takes in queue of last 'n' head positions (gaze_history), 
    the minimum number of position changes to qualify for a shake/nod (shake_threshold),
    and the number of frames this needs to occur within to count as a shake/nod (time_window)
"""
def detect_head_shake_nod(gaze_history, shake_threshold, time_window):
    if len(gaze_history) < time_window:
        return False
    
    # For a set number of stored frames, check the total times the head position changes from left<->right or up<->down
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