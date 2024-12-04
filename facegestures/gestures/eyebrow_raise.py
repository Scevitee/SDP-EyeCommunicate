import imutils
from imutils import face_utils
import numpy as np
from statistics import mean



# Get the average coordinates of the eyes and the eyebrows
# Find the distance between them
def calculate_eyebrow_distance(face_landmarks):
    (leStart, leEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
    (reStart, reEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    left_eyebrow = face_landmarks[leStart:leEnd]
    right_eyebrow = face_landmarks[reStart:reEnd]
    left_eye = face_landmarks[lStart:lEnd]
    right_eye = face_landmarks[rStart:rEnd]
    
    left_eyebrow_avg = np.mean(left_eyebrow, axis=(0, 1))
    right_eyebrow_avg = np.mean(right_eyebrow, axis=(0, 1))
    left_eye_avg = np.mean(left_eye, axis=(0, 1))
    right_eye_avg = np.mean(right_eye, axis=(0, 1))
    
    left_brow_eye_dist = np.linalg.norm(left_eyebrow_avg - left_eye_avg)
    right_brow_eye_dist = np.linalg.norm(right_eyebrow_avg - right_eye_avg)
    
    return (left_brow_eye_dist + right_brow_eye_dist) / 2



def detect_eyebrow_raise(face_landmarks, shared_state, eyeb_raise_consec_frames=3):

    eyebrow_dist_avg = calculate_eyebrow_distance(face_landmarks)

    # left_check_cheek = np.linalg.norm(left_eyebrow_avg - left_cheek)
    # right_check_cheek = np.linalg.norm(right_eyebrow_avg - right_cheek)

    # If the ratio of the eyebrow to eye/nose is greater than the threshold, 
    # increment the eyebrow counter
    if eyebrow_dist_avg > (shared_state.calibrated_eyebrow_distance * shared_state.EYEBROW_SCALAR):
        shared_state.eyebrow_counter += 1
        
        # checking for consectutive frames of eyebrow being above the threshold
        if shared_state.eyebrow_counter >= eyeb_raise_consec_frames:
            # print(f"Avg eyebrow-eye distance: {eyebrow_dist_avg}")
            shared_state.eyebrow_counter = 0
            return True
    else:
        shared_state.eyebrow_counter = 0
        return False
        
        
