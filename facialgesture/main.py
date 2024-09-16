import cv2
import dlib
import face_recognition
import numpy as np
from imutils import face_utils
from imutils.video import VideoStream
import imutils

# 2. Initialize the webcam
cap = VideoStream(src=0).start()

# 3. Load the face detector and facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

blink_counter = 0
eyebrow_counter = 0


# 4. Define gesture detection functions
def detect_blink(face_landmarks, eye_ar_threshold=0.2, eye_ar_consec_frames=4):
    global blink_counter

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
    ear = (left_ear + right_ear) / 2.0

    # Check to see if the eye aspect ratio is below the blink threshold
    if ear < eye_ar_threshold:
        blink_counter += 1

    else:
        if blink_counter >= eye_ar_consec_frames:
            return True


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
while True:
    frame = cap.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = detector(gray, 0)

    for face in faces:
        # Get facial landmarks
        landmarks = predictor(frame, face)
        landmarks = face_utils.shape_to_np(landmarks)

        # Check for specific gestures
        if detect_blink(landmarks):
            print('Blink detected!')
            blink_counter = 0

        if detect_eyebrow_raise(landmarks):
            print('Eyebrow raise detected!')
            eyebrow_counter = 0

    # Display the frame for debugging
    cv2.imshow('Facial Gesture Control', frame)

    # Click Q while focused on frame to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 6. Clean up
cv2.destroyAllWindows()
cap.stop()
