import cv2
import numpy as np

from .ULFD import UltraLightFaceDetection
from .DFL import DepthFacialLandmarks
from .pose_related_detections import *


def rotationMatrixToEulerAngles(R):
    '''
    Ref: https://stackoverflow.com/a/15029416
    '''
    sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)

    if sy < 1e-6:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0
    else:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])

    return np.degrees([x, y, z])


def build_projection_matrix(rear_size, factor=np.sqrt(2)):
    rear_depth = 0
    front_size = front_depth = factor * rear_size

    projections = np.array([
        [-rear_size, -rear_size, rear_depth],
        [-rear_size, rear_size, rear_depth],
        [rear_size, rear_size, rear_depth],
        [rear_size, -rear_size, rear_depth],
        [-front_size, -front_size, front_depth],
        [-front_size, front_size, front_depth],
        [front_size, front_size, front_depth],
        [front_size, -front_size, front_depth],
    ], dtype=np.float32)

    return projections


def draw_projection(frame, R, landmarks, color, thickness=2):
    # build projection matrix
    radius = np.max(np.max(landmarks, 0) - np.min(landmarks, 0)) // 2
    projections = build_projection_matrix(radius)

    # refine rotate matrix
    rotate_matrix = R[:, :2]
    rotate_matrix[:, 1] *= -1

    # 3D -> 2D
    center = np.mean(landmarks[:27], axis=0)
    points = projections @ rotate_matrix + center
    points = points.astype(np.int32)

    # draw poly
    cv2.polylines(frame, np.take(points, [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [0, 4], [1, 5], [2, 6], [3, 7],
        [4, 5], [5, 6], [6, 7], [7, 4]
    ], axis=0), False, color, thickness, cv2.LINE_AA)


def draw_poly(frame, landmarks, color=(128, 255, 255), thickness=1):
    cv2.polylines(frame, [
        landmarks[:17],
        landmarks[17:22],
        landmarks[22:27],
        landmarks[27:31],
        landmarks[31:36]
    ], False, color, thickness=thickness)
    cv2.polylines(frame, [
        landmarks[36:42],
        landmarks[42:48],
        landmarks[48:60],
        landmarks[60:]
    ], True, color, thickness=thickness)


def sparse(frame, results, color):
    landmarks = np.round(results[0]).astype(np.int)
    for p in landmarks:
        cv2.circle(frame, tuple(p), 2, color, 0, cv2.LINE_AA)
    draw_poly(frame, landmarks, color=color)


def dense(frame, results, color):
    landmarks = np.round(results[0]).astype(np.int)
    for p in landmarks[::6, :2]:
        cv2.circle(frame, tuple(p), 1, color, 0, cv2.LINE_AA)


def mesh(frame, results, color):
    landmarks = results[0].astype(np.float32)
    color.render(landmarks.copy(), frame)


def pose(frame, results, color):
    landmarks, params = results

    # rotate matrix
    R = params[:3, :3].copy()

    # decompose matrix to ruler angle
    euler = rotationMatrixToEulerAngles(R)
    # print(f"Pitch: {euler[0]}; Yaw: {euler[1]}; Roll: {euler[2]};")

    draw_projection(frame, R, landmarks, color)


# Determines gaze direction based on yaw and pitch
# Takes in the current frame and face mesh results, optional param to adjust thresholds
# Threshold format: (left_thresh, right_thresh, up_thresh, down_thresh)
# Returns (horizontal, vertical) values,
# for horiz: -1 = left, 0 = center, 1 = right |
# for vert: -1 = down, 0 = center, 1 = up
def get_gaze_direction(frame, results, thresholds=(19, -19, 17, -10)):
    (left_thresh, right_thresh, up_thresh, down_thresh) = thresholds

    landmarks, params = results

    euler = rotationMatrixToEulerAngles(params[:3, :3].copy())

    yaw = euler[1]
    pitch = euler[0]

    horiz = 0
    vert = 0

    if yaw < right_thresh:
        horiz = 1
    elif yaw > left_thresh:
        horiz = -1
    else:
        horiz = 0

    if pitch > up_thresh:
        vert = 1
    elif pitch < down_thresh:
        vert = -1
    else:
        vert = 0

    return horiz, vert


# NEEDS MORE TESTING (possibly even calibration setting)
def draw_gaze_direction(frame, results):
    landmarks, params = results

    (horiz, vert) = get_gaze_direction(frame, results)

    if horiz == 1:
        horiz_text = "Right"
    elif horiz == -1:
        horiz_text = "Left"
    else:
        horiz_text = "Center"

    if vert == 1:
        vert_text = "Up"
    elif vert == -1:
        vert_text = "Down"
    else:
        vert_text = "Center"

    text_size_horiz = cv2.getTextSize(horiz_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
    text_size_vert = cv2.getTextSize(vert_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]

    text_x_horiz = (frame.shape[1] - text_size_horiz[0]) // 3
    # test_x_vert = (frame.shape[1] - text_size_vert[0]) // 2

    text_y_horiz = 30
    test_y_vert = 60

    cv2.putText(frame, f"Horizontal: {horiz_text}", (text_x_horiz, text_y_horiz), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)
    cv2.putText(frame, f"Vertical: {vert_text}", (text_x_horiz, test_y_vert), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                2)