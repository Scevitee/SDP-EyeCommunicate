import pygame
import cv2
from eyeGestures.eyegestures import EyeGestures_v2
from eyeGestures.utils import VideoCapture
import pyautogui
import time

def main():
    cap = VideoCapture(0)  # Use the default webcam

    framerate = 60
    radius = 400
    total_iterations = 25  # Total number of calibration points

    eye_gestures = EyeGestures_v2(radius)
    eye_gestures.setClassicalImpact(2)
    eye_gestures.setFixation(1.0)

    # Initialize Pygame
    pygame.init()
    pygame.font.init()

    # Get the display dimensions
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h

    # Define colors
    BACKGROUND_COLOR = (30, 30, 30)
    CALIBRATION_POINT_COLOR = (50, 49, 121)
    GAZE_POINT_COLOR = (80, 200, 120)
    TEXT_COLOR = (185, 185, 185)

    # Set up the screen
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Eye Tracker Calibration")

    # Load fonts with custom sizes
    font_size = 80  # Increase the font size for the pre-calibration message
    bold_font_size = 90  # Increase the font size for the countdown
    font = pygame.font.Font(None, font_size)
    bold_font = pygame.font.Font(None, bold_font_size)
    bold_font.set_bold(True)

    clock = pygame.time.Clock()

    # Optimize PyAutoGUI
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    iterator = 1
    prev_x = 0
    prev_y = 0

    # Pre-calibration message
    pre_calibration_message_line1 = "Hello! Your eye-tracking calibration is about to begin."
    pre_calibration_message_line2 = "Please try to keep your head as still as possible and focus on the number in the center of the dots."
    countdown = 6

    # Display pre-calibration message with countdown
    for i in range(countdown, -1, -1):
        screen.fill(BACKGROUND_COLOR)
        
        # Render the first line of the pre-calibration message
        message_surface_line1 = font.render(pre_calibration_message_line1, True, TEXT_COLOR)
        message_rect_line1 = message_surface_line1.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
        screen.blit(message_surface_line1, message_rect_line1)
        
        # Render the second line of the pre-calibration message
        message_surface_line2 = font.render(pre_calibration_message_line2, True, TEXT_COLOR)
        message_rect_line2 = message_surface_line2.get_rect(center=(screen_width // 2, screen_height // 2 - 40))
        screen.blit(message_surface_line2, message_rect_line2)
        
        # Render the countdown
        countdown_surface = bold_font.render(str(i), True, TEXT_COLOR)
        countdown_rect = countdown_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
        screen.blit(countdown_surface, countdown_rect)
        
        pygame.display.flip()
        time.sleep(1)

    calibrating = True

    # Calibration Loop
    while calibrating:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gevent, cevent = eye_gestures.step(
            frame,
            calibration=True,
            width=screen_width,
            height=screen_height,
            context="main"
        )

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                calibrating = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    calibrating = False

        # Calibration display
        screen.fill(BACKGROUND_COLOR)

        # Draw calibration point
        pygame.draw.circle(screen, CALIBRATION_POINT_COLOR, cevent.point, cevent.acceptance_radius)

        # Draw gaze point
        pygame.draw.circle(screen, GAZE_POINT_COLOR, gevent.point, 30)

        # Display iterator number in the center of the calibration point
        iterator_text = f"{iterator}/{total_iterations}"
        text_surface = bold_font.render(iterator_text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=cevent.point)
        screen.blit(text_surface, text_rect)

        # Display instructions at the top
        instructions = "Focus on the dot to calibrate"
        instructions_surface = font.render(instructions, True, TEXT_COLOR)
        instructions_rect = instructions_surface.get_rect(center=(screen_width // 2, 50))
        screen.blit(instructions_surface, instructions_rect)

        if cevent.point[0] != prev_x or cevent.point[1] != prev_y:
            iterator += 1
            prev_x = cevent.point[0]
            prev_y = cevent.point[1]

        if iterator > total_iterations:
            calibrating = False

        pygame.display.flip()
        clock.tick(framerate)

    pygame.quit()

    # Tracking Loop
    tracking = True
    while tracking:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gevent, _ = eye_gestures.step(
            frame,
            calibration=False,
            width=screen_width,
            height=screen_height,
            context="main"
        )

        if gevent is not None:
            gaze_point = gevent.point  # (x, y) coordinates
            # Ensure the gaze point is within screen bounds
            x = min(max(int(gaze_point[0]), 0), screen_width - 1)
            y = min(max(int(gaze_point[1]), 0), screen_height - 1)
            pyautogui.moveTo(x, y)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()