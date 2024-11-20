



# For a given axis (horizontal or vertical), we can count the number of direction changes. If this exceeds some amount, we say a shake or nod has occurred
def detect_shake_nod(gaze_history, shake_nod_threshold, time_window):
    if len(gaze_history) < time_window:
        return False
    
    # For a set number of stored frames, check the total times the head position changes from left<->right or up<->down
    direction_changes = sum(1 for i in range(1, len(gaze_history)) if gaze_history[i] != gaze_history[i-1] and gaze_history[i] != 0)
    
    return direction_changes >= shake_nod_threshold


def detect_look_left_right(left_right_history, direction):
    if direction == 'left':
        return all(x == 1 for x in left_right_history)
    if direction == 'right':
        return all(x == -1 for x in left_right_history)
    else:
        print("Invalid direction |  enter either  'left' or 'right'")

def detect_look_up_down(up_down_history, direction):
    if direction == 'up':
        return all(x == 1 for x in up_down_history)
    if direction == 'down':
        return all(x == -1 for x in up_down_history)
    else:
        print("Invalid direction  |  enter either 'up' or 'down'")


def draw_shake_nod(frame, shake_detected, nod_detected):

    if shake_detected:
        cv2.putText(frame, "Head Shake Detected!", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    if nod_detected:
        cv2.putText(frame, "Head Nod Detected!", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        