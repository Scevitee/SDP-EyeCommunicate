import pygame
import cv2
# import numpy as np
from eyeGestures.eyegestures import EyeGestures_v2
from eyeGestures.utils import VideoCapture
import pyautogui


def main():

    cap = VideoCapture(0)  # Use the default webcam

    framerate = 60
    radius = 500

    eye_gestures = EyeGestures_v2(radius)
    eye_gestures.setClassicalImpact(2)
    eye_gestures.setFixation(1.0)
    calib = True
    end_calib = True

    # Create a fullscreen window

    pygame.init()
    pygame.font.init()

    # Get the display dimensions
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h

    # RED = (255, 0, 100)
    GREEN = (0, 255, 0)
    # BLANK = (0, 0, 0)
    BLUE = (100, 0, 255)
    WHITE = (255, 255, 255)

    # Set up the screen
    window_name = "EyeGestures Test - Eye Coordinates"
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption(window_name)
    font_size = 48
    bold_font = pygame.font.Font(None, font_size)
    bold_font.set_bold(True)  # Set the font to bold

    clock = pygame.time.Clock()

    pyautogui.FAILSAFE = False

    iterator = 0
    prev_x = 0
    prev_y = 0
    track = True

    while track:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # cv2.imwrite('frame.jpg', frame)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Call the step method and unpack two returned objects
        gevent, cevent = eye_gestures.step(
            frame,
            calibration=calib,
            width=screen_width,
            height=screen_height,
            context="main"
        )

        if gevent is not None and not calib:
            gaze_point = gevent.point  # (x, y) coordinates
            pyautogui.moveTo(int(gaze_point[0]), int(gaze_point[1]))  # add this in when it is more stable
            if end_calib:
                pygame.quit()
                end_calib = False
        elif calib:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    track = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        track = False

            screen.fill((0, 0, 0))
            # # this section is to display the camera frames
            # # uncomment the numpy import at the top as well for use
            # frame = np.rot90(frame)
            # frame = pygame.surfarray.make_surface(frame)
            # frame = pygame.transform.scale(frame, (400, 400))
            # screen.blit(frame, (0, 0))

            my_font = pygame.font.SysFont('Comic Sans MS', 30)
            text_surface = my_font.render(f'{gevent.fixation}', False, (0, 0, 0))
            screen.blit(text_surface, (0, 0))

            text_surface = bold_font.render(f"{iterator}/{25}", True, WHITE)
            text_square = text_surface.get_rect(center=cevent.point)
            screen.blit(text_surface, text_square)

            pygame.draw.circle(screen, BLUE, cevent.point, cevent.acceptance_radius)
            pygame.draw.circle(screen, GREEN, gevent.point, 50)

            text_surface = bold_font.render(f"{iterator}/{25}", True, WHITE)
            text_square = text_surface.get_rect(center=cevent.point)
            screen.blit(text_surface, text_square)


            if cevent.point[0] != prev_x or cevent.point[1] != prev_y:
                iterator += 1
                prev_x = cevent.point[0]
                prev_y = cevent.point[1]

            calib = (iterator <= 25)
            pygame.display.flip()

        clock.tick(framerate)

    pygame.quit()



if __name__ == "__main__":
    main()
