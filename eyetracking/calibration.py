def Calibrate(cap, width, height):

    eye_gestures = EyeGestures_v2(calibration_radius=1000)

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
