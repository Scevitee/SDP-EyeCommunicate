import cv2
# import pygame
from eyeGestures.eyegestures import EyeGestures_v2
from eyeGestures.utils import VideoCapture
import pyautogui

def main():

    # Retrieve screen dimensions
    # screen_width, screen_height = pyautogui.size()
    screen_width = 3440
    screen_height = 1440

    cap = VideoCapture(0)  # Use the default webcam
    # eye_gestures = Calibrate(cap, screen_width, screen_height)

    radius = 500
    eye_gestures = EyeGestures_v2(radius)
    calib = True

    # Create a fullscreen window
    window_name = "EyeGestures Test - Eye Coordinates"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # cv2.setWindowProperty(window_name, 1920, 1080)

    iterator = 0
    prev_x = 0
    prev_y = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Call the step method and unpack two returned objects
        gevent, cevent = eye_gestures.step(
            frame,
            calibration=calib,
            width=screen_width,
            height=screen_height,
            context="main"
        )


        if calib:
            print(cevent.point[0])
            print(cevent.point[1])
            cv2.circle(frame, (int(cevent.point[0]), int(cevent.point[1])), radius, (255, 255, 0), -1)
            calib = (iterator <= 25)
            if cevent.point[0] != prev_x or cevent.point[1] != prev_y:
                iterator += 1
                prev_x = cevent.point[0]
                prev_y = cevent.point[1]


        if gevent is not None:
            gaze_point = gevent.point  # (x, y) coordinates

            # Display the gaze point on the frame
            cv2.circle(frame, (int(gaze_point[0]), int(gaze_point[1])), 10, (0, 255, 0), -1)
            cv2.putText(frame, f"Gaze: ({int(gaze_point[0])}, {int(gaze_point[1])})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # pyautogui.moveTo(int(gaze_point[0]), int(gaze_point[1]))  # add this in when it is more stable

        # Show the frame with annotations
        cv2.imshow(window_name, frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
