import numpy as np
from imutils import face_utils

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
