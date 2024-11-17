import cv2
import pygame
from eyeGestures.eyegestures import EyeGestures_v2
# from calibration import Calibrate
import pyautogui

def main():
    cap = cv2.VideoCapture(0)  # Use the default webcam

    # Retrieve screen dimensions
    screen_width, screen_height = pyautogui.size()

    eye_gestures = Calibrate(screen_width, screen_height)

    # Create a fullscreen window
    window_name = "EyeGestures Test - Eye Coordinates"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # cv2.setWindowProperty(window_name, 1920, 1080)

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


def Calibrate(width, height):

    eye_gestures = EyeGestures_v2(calibration_radius=1000)
    cap = cv2.VideoCapture(0)  # Use the default webcam

    # Initialize Pygame
    pygame.init()

    # Set up the screen
    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
    pygame.display.set_caption("Fullscreen Red Cursor")

    clock = pygame.time.Clock()

    # RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)

    # Main game loop
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False

        ret, frame = cap.read()
        if not ret or frame.shape[0] == 0:
            print("Frame not loaded")
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        gevent, cevent = eye_gestures.step(
            frame,
            calibration=True,
            width=width,
            height=height,
            context="main"
        )


        # grab current point
        point = cevent.point
        gaze = gevent.point

        # Display frame on Pygame screen
        pygame.draw.circle(screen, YELLOW, point, 200)
        pygame.draw.circle(screen, BLUE, gaze, 50)

        # Cap the frame rate
        clock.tick(10)
        pygame.draw.circle(screen, GREEN, point, 200)

    pygame.quit()
    return eye_gestures


if __name__ == "__main__":
    main()
