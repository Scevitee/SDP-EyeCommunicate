import cv2
import dlib
import face_recognition
import numpy as np
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import time
from collections import deque

# 2. Initialize the webcam
cap = VideoStream(src=0).start()

# 3. Load the face detector and facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# instantiate some global vars
blink_counter = 0
eyebrow_counter = 0
ear_list = []
# initialize queue with high values for the first few frames
BLINK_QUEUE_SIZE = 8

blink_queue = deque([1] * BLINK_QUEUE_SIZE, maxlen=BLINK_QUEUE_SIZE)

buffer_frames = 0
BUFFER_DURATION = 50  


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


# 4. Define gesture detection functions
def detect_blink(face_landmarks, eye_ar_threshold):
    global blink_counter, buffer_frames
    
    ear = calculate_ear(face_landmarks)
    blink_queue.append(ear)
    
    if buffer_frames > 0:
        buffer_frames -= 1
        return False



    if np.mean(blink_queue) < eye_ar_threshold:
        print(f"Blink detected! EAR: {np.mean(blink_queue)}")
        buffer_frames = BUFFER_DURATION
        return True

    return False

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


# 5. Loop
bct = 0
calibrated_ear = 0
ear_list = []
calibration_time = 2.5  # seconds
start_time = time.time()
calibrating = True

while True:

    frame = cap.read()
    frame = imutils.resize(frame, width=500)
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
                # choosing a low percentile instead of min() to protect against
                # edge case of a blink during the calibration period
                calibrated_ear = 0.76 * np.percentile(ear_list, 5)
                print(f"Calibrated EAR: {calibrated_ear}")
                calibrating = False

        else:

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)

            for (i, (x, y)) in enumerate(landmarks):
                # draw circles at the position of the facial landmarks
                cv2.circle(frame, (x, y), 1, (0, 255, 0), 1)

                # draw the number corresponding the landmark position
                # cv2.putText(frame, f"{i + 1}", (x, y), 1, .5, 1, 1)

            # Check for specific gestures
            if detect_blink(landmarks, calibrated_ear):  
                bct += 1
                print(f"Blink count: {bct}")


            if detect_eyebrow_raise(landmarks):
                # print('Eyebrow raise detected!')
                eyebrow_counter = 0

    # Display the frame for debugging
    cv2.imshow('Facial Gesture Control', frame)

    # Click Q while focused on frame to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 6. Clean up
cv2.destroyAllWindows()
cap.stop()
