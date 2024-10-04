import  cv2
import numpy as np
from imutils import face_utils
from imutils.video import VideoStream
import imutils
import dlib
from collections import deque
from gesture_helpers import *


SHAKE_THRESHOLD = 4  # Number of direction changes to consider a head shake
NOD_THRESHOLD = 4  # Number of direction changes to consider a nod
TIME_WINDOW = 20     # Number of frames to consider for head shake detection
shake_history = deque(maxlen=TIME_WINDOW)
nod_history = deque(maxlen=TIME_WINDOW)

cap = VideoStream(src=0).start()
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# These are the 3D points of the face landmarks. These are approximations.
# Should look into ways to get better estimates of the 3D points -- may improve accuracy -- further testing needed to determine if this is necessary
model_points = np.array([
    (0.0, 0.0, 0.0),             # Nose tip
    (0.0, -330.0, -65.0),        # Chin
    (-225.0, 170.0, -135.0),     # Left eye left corner
    (225.0, 170.0, -135.0),      # Right eye right corne
    (-150.0, -150.0, -125.0),    # Left Mouth corner
    (150.0, -150.0, -125.0)      # Right mouth corner
])

while True:
    frame = cap.read()
    frame = imutils.resize(frame, width=1200)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    size = frame.shape
    
    # Using an approximation of the camera specs / camera matrix
    focal_length = size[1]
    center = (size[1]/2, size[0]/2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]], dtype = "double"
    )

    for face in detector(gray, 0):
        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)

        headpose_points = get_headpose_points(landmarks)

        dist_coeffs = np.zeros((4,1))
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, headpose_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

        gaze_direction_horiz, gaze_direction_vert = get_gaze_direction(rotation_vector)
        shake_history.append(gaze_direction_horiz)
        nod_history.append(gaze_direction_vert)
        
        is_shaking_head = detect_head_shake_nod(shake_history, SHAKE_THRESHOLD, TIME_WINDOW)
        is_nodding_head = detect_head_shake_nod(nod_history, NOD_THRESHOLD, TIME_WINDOW)
        
        if is_shaking_head:
            cv2.putText(frame, "Head Shake Detected!", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if is_nodding_head:
            cv2.putText(frame, "Head Nod Detected!", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        horiz_text = "Left" if gaze_direction_horiz == -1 else "Right" if gaze_direction_horiz == 1 else "Center"
        vert_text = "Down" if gaze_direction_vert == -1 else "Up" if gaze_direction_vert == 1 else "Center"
        
        text_size_horiz = cv2.getTextSize(horiz_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_size_vert = cv2.getTextSize(vert_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        
        text_x_horiz = (frame.shape[1] - text_size_horiz[0]) // 2
        test_x_vert = (frame.shape[1] - text_size_vert[0]) // 2
        
        text_y_horiz = 30
        test_y_vert = 60
        
        cv2.putText(frame, f"Horizontal: {horiz_text}", (text_x_horiz, text_y_horiz), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Vertical: {vert_text}", (test_x_vert, test_y_vert), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        for p in headpose_points:
            cv2.circle(frame, (int(p[0]), int(p[1])), 3, (0,0,255), -1)
        
        # Draw nose direction
        (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rotation_vector, translation_vector, camera_matrix, dist_coeffs)
        p1 = (int(headpose_points[0][0]), int(headpose_points[0][1]))
        p2 = (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
        cv2.line(frame, p1, p2, (255,0,0), 2)

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
cap.stop()

