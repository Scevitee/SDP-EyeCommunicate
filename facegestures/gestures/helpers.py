# Helper functions for gesture detection
import  numpy as np
import  cv2
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import dlib
import mediapipe as mp

"""
    Random Helper Functions
"""
def dense_to_dlib(arr):
    rects = dlib.rectangles()
    for row in arr:
        left, top, right, bottom = map(int, row)
        rects.append(dlib.rectangle(left, top, right, bottom))
    return rects

def dlib_to_dense(rects):
    arr = np.zeros((len(rects), 4))
    for i, rect in enumerate(rects):
        arr[i] = [rect.left(), rect.top(), rect.right(), rect.bottom()]
    return arr

def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 
    
# def change_sensitivity(shared_state, var_name, amount, increase=True):
#     # Get current value of the class variable
#     current_value = getattr(shared_state, var_name)
    
#     # Check if the current value is a number (for incrementing)
#     if isinstance(current_value, (int, float)):
#         # Increment the variable by the specified amount (bound between 0-1)
#         if increase:
#             setattr(shared_state, var_name, round(clamp(current_value + amount, 0, 1), 4))
#         else:
#             setattr(shared_state, var_name, round(clamp(current_value - amount, 0, 1), 4))
            
#         print(f"{var_name}: {getattr(shared_state, var_name)}")
#     else:
#         print(f"Error: {var_name} is not a number and cannot be incremented.")

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
     EYEBROW RAISE DETECTION
"""


