import cv2
from eyegestures import EyeGestures_v2
import pyautogui

def main():
    eye_gestures = EyeGestures_v2(calibration_radius=1000)
    cap = cv2.VideoCapture(0)  # Use the default webcam

    # Retrieve screen dimensions
    screen_width, screen_height = pyautogui.size()

    # Create a fullscreen window
    window_name = "EyeGestures Test - Eye Coordinates"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Call the step method and unpack two returned objects
        gevent, cevent = eye_gestures.step(
            frame,
            calibration=False,
            width=screen_width,    
            height=screen_height,  
            context="main"
        )

        if gevent is not None:
            gaze_point = gevent.point  # (x, y) coordinates

            # Display the gaze point on the frame
            cv2.circle(frame, (int(gaze_point[0]), int(gaze_point[1])), 10, (0, 255, 0), -1)
            cv2.putText(frame, f"Gaze: ({int(gaze_point[0])}, {int(gaze_point[1])})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show the frame with annotations
        cv2.imshow(window_name, frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
