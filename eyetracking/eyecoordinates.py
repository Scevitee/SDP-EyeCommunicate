# The following code was copied from 'inference.core.interfaces.stream.sinks' module
# in the 'inference' package (version 0.18.1).

# The copied functions were necessary for the modified function to work properly
# The modified function that we use is the final one, `render_boxes_with_info`

# Modifications:
# Added logging to print prediction values in the terminal.

import json
import socket
from datetime import datetime
from functools import partial
from typing import Callable, List, Optional, Tuple, Union

import pyautogui
import cv2
import numpy as np
import supervision as sv
from supervision.annotators.base import BaseAnnotator

from inference.core import logger
from inference.core.active_learning.middlewares import ActiveLearningMiddleware
from inference.core.interfaces.camera.entities import VideoFrame
from inference.core.interfaces.stream.entities import SinkHandler
from inference.core.interfaces.stream.utils import wrap_in_list
from inference.core.utils.drawing import create_tiles
from inference.core.utils.preprocess import letterbox_image

DEFAULT_BBOX_ANNOTATOR = sv.BoxAnnotator()
DEFAULT_LABEL_ANNOTATOR = sv.LabelAnnotator()
DEFAULT_FPS_MONITOR = sv.FPSMonitor()

ImageWithSourceID = Tuple[Optional[int], np.ndarray]


# This function was copied from the 'inference.core.interfaces.stream.sinks' module.
def display_image(image: Union[ImageWithSourceID, List[ImageWithSourceID]]) -> None:
    if issubclass(type(image), list):
        tiles = create_tiles(images=[i[1] for i in image])
        cv2.imshow("Predictions - tiles", tiles)
    else:
        source_id, picture_to_display = image
        if source_id is None:
            source_id = "N/A"
        cv2.imshow(f"Predictions - video: {source_id}", picture_to_display)
    cv2.waitKey(1)

# This function was copied from the 'inference.core.interfaces.stream.sinks' module.
def _handle_frame_rendering(
    frame: Optional[VideoFrame],
    prediction: dict,
    annotators: List[BaseAnnotator],
    display_size: Optional[Tuple[int, int]],
    display_statistics: bool,
    fps_value: Optional[float],
) -> np.ndarray:
    if frame is None:
        image = np.zeros((256, 256, 3), dtype=np.uint8)
    else:
        try:
            labels = [p["class"] for p in prediction["predictions"]]
            if hasattr(sv.Detections, "from_inference"):
                detections = sv.Detections.from_inference(prediction)
            else:
                detections = sv.Detections.from_inference(prediction)
            image = frame.image.copy()
            for annotator in annotators:
                kwargs = {
                    "scene": image,
                    "detections": detections,
                }
                if isinstance(annotator, sv.LabelAnnotator):
                    kwargs["labels"] = labels
                image = annotator.annotate(**kwargs)
        except (TypeError, KeyError):
            logger.warning(
                f"Used `render_boxes(...)` sink, but predictions that were provided do not match the expected "
                f"format of object detection prediction that could be accepted by "
                f"`supervision.Detection.from_inference(...)"
            )
            image = frame.image.copy()
    if display_size is not None:
        image = letterbox_image(image, desired_size=display_size)
    if display_statistics:
        image = render_statistics(
            image=image,
            frame_timestamp=(frame.frame_timestamp if frame is not None else None),
            fps=fps_value,
        )
    return image

# This function was copied from the 'inference.core.interfaces.stream.sinks' module.
def render_statistics(
    image: np.ndarray, frame_timestamp: Optional[datetime], fps: Optional[float]
) -> np.ndarray:
    image_height = image.shape[0]
    if frame_timestamp is not None:
        latency = round((datetime.now() - frame_timestamp).total_seconds() * 1000, 2)
        image = cv2.putText(
            image,
            f"LATENCY: {latency} ms",
            (10, image_height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
    if fps is not None:
        fps = round(fps, 2)
        image = cv2.putText(
            image,
            f"THROUGHPUT: {fps}",
            (10, image_height - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
    return image


# This is the modified function that we are using based on 'render_boxes'
def render_boxes_with_info(
    predictions: Union[dict, List[Optional[dict]]],
    video_frame: Union[VideoFrame, List[Optional[VideoFrame]]],
    annotator: Union[BaseAnnotator, List[BaseAnnotator]] = None,
    display_size: Optional[Tuple[int, int]] = (1280, 720),
    fps_monitor: Optional[sv.FPSMonitor] = DEFAULT_FPS_MONITOR,
    display_statistics: bool = False,
    on_frame_rendered: Callable[
        [Union[ImageWithSourceID, List[ImageWithSourceID]]], None
    ] = display_image,
) -> None:
    """
    Helper tool to render object detection predictions on top of video frame and print the details in the terminal.
    """
    sequential_input_provided = False
    if not isinstance(video_frame, list):
        sequential_input_provided = True
    video_frame = wrap_in_list(element=video_frame)
    predictions = wrap_in_list(element=predictions)
    if annotator is None:
        annotator = [
            DEFAULT_BBOX_ANNOTATOR,
            DEFAULT_LABEL_ANNOTATOR,
        ]
    fps_value = None
    if fps_monitor is not None:
        ticks = sum(f is not None for f in video_frame)
        for _ in range(ticks):
            fps_monitor.tick()
        if hasattr(fps_monitor, "fps"):
            fps_value = fps_monitor.fps
        else:
            fps_value = fps_monitor()
    images: List[ImageWithSourceID] = []
    annotators = annotator if isinstance(annotator, list) else [annotator]
    for idx, (single_frame, frame_prediction) in enumerate(
        zip(video_frame, predictions)
    ):
        image = _handle_frame_rendering(
            frame=single_frame,
            prediction=frame_prediction,
            annotators=annotators,
            display_size=display_size,
            display_statistics=display_statistics,
            fps_value=fps_value,
        )

        # Modified portion of the function
        eye_predict = []
        gaze_predict = []
        # Loop through predictions and print prediction info to terminal
        if isinstance(frame_prediction, dict) and 'predictions' in frame_prediction:
            for prediction in frame_prediction['predictions']:
                x = prediction.get("x", 0)
                y = prediction.get("y", 0)
                # width = prediction.get("width", 0)
                # height = prediction.get("height", 0)
                # confidence = prediction.get("confidence", 0)
                class_name = prediction.get("class", "unknown")

                # Print details to terminal
                # print(f"Class: {class_name}, Confidence: {confidence:.2f}, (x: {x}, y: {y}, width: {width}, height: {height})")
                if class_name == "eye":
                    eye_predict.append(x)
                    eye_predict.append(y)
                elif class_name == "gaze":
                    gaze_predict.append(x)
                    gaze_predict.append(y)

        global calibrate
        global initialized
        if calibrate and len(eye_predict) == 4 and len(gaze_predict) == 4:
            calibration(eye_predict, gaze_predict)

        if not initialized:
            global cal_points
            match cal_points:
                case 0:
                    screenPoints()
                    print("bring up calibration image and look at the first dot at the top left. KEEP YOUR HEAD STILL!")
                    print("with each calibration step move ONLY your eyes to the next dot and press enter")
                    input("1. Press enter to begin calibration")
                case 1:
                    input("2. Gaze at second dot and press enter")
                case 2:
                    input("3. Gaze at third dot and press enter")
                case 3:
                    input("4. Gaze at fourth dot and press enter")
                case 4:
                    input("5. Gaze at fifth dot and press enter")
                case 5:
                    input("6. Gaze at sixth dot and press enter")
                case 6:
                    input("7. Gaze at seventh dot and press enter")
                case 7:
                    input("8. Gaze at eighth dot and press enter")
                case 8:
                    input("9. Gaze at ninth dot and press enter")
            calibrate = True
            initialized = True

        screen_coords(eye_predict, gaze_predict)
        # End of modified code
        images.append((idx, image))
    if sequential_input_provided:
        on_frame_rendered((video_frame[0].source_id, images[0][1]))
    else:
        on_frame_rendered(images)


calibrate = False
initialized = False
cal_points = 0
xCal_points = []
yCal_points = []
xRef = []
yRef = []


def screenPoints():
    global xCal_points
    global yCal_points
    screenSize = pyautogui.size()
    width = screenSize[0]
    height = screenSize[1]
    xCal_points = [width/2, width-50]
    yCal_points = [height/2, height-50]
    # xCal_points = [50, width/2, width-50, 50, width/2, width-50, 50, width/2, width-50]
    # yCal_points = [50, 50, 50, height/2, height/2, height/2, height-50, height-50, height-50]
    # xCal_points.append(50)
    # yCal_points.append(50)
    # xCal_points.append(width / 2)
    # yCal_points.append(50)
    # xCal_points.append(width - 50)
    # yCal_points.append(50)
    # xCal_points.append(50)
    # yCal_points.append(height / 2)
    # xCal_points.append(width / 2)
    # yCal_points.append(height / 2)
    # xCal_points.append(width - 50)
    # yCal_points.append(height / 2)
    # xCal_points.append(50)
    # yCal_points.append(height - 50)
    # xCal_points.append(width / 2)
    # yCal_points.append(height - 50)
    # xCal_points.append(width - 50)
    # yCal_points.append(height - 50)


def trans_coords(eye_predict, gaze_predict):
    try_x1 = abs(eye_predict[0] - gaze_predict[0])
    try_x2 = abs(eye_predict[0] - gaze_predict[2])
    coords = []

    if try_x1 > try_x2:
        x1 = try_x2
        y1 = abs(eye_predict[1] - gaze_predict[3])
        x2 = abs(eye_predict[2] - gaze_predict[0])
        y2 = abs(eye_predict[3] - gaze_predict[1])
    elif try_x2 > try_x1:
        x1 = try_x1
        y1 = abs(eye_predict[1] - gaze_predict[1])
        x2 = abs(eye_predict[2] - gaze_predict[2])
        y2 = abs(eye_predict[3] - gaze_predict[3])

    # this is a bandaid will have to change this method
    coords.append((x1 + x2) / 2.0)
    coords.append((y1 + y2) / 2.0)

    return coords


def calibration(eye_predict, gaze_predict):
    global cal_points
    global calibrate
    global initialized
    eye_coords = trans_coords(eye_predict, gaze_predict)
    xRef.append(eye_coords[0])
    yRef.append(eye_coords[1])
    cal_points += 1
    calibrate = False
    if cal_points != 9:
        initialized = False


def screen_coords(eye_predict, gaze_predict):
    if (len(eye_predict) == 4 and len(gaze_predict) == 4):
        eye_coords = trans_coords(eye_predict, gaze_predict)

        if eye_coords[0] < xRef[4]:
            if eye_coords[1] < yRef[4]:
                top_left(eye_coords[0], eye_coords[1])
            elif eye_coords[1] > yRef[4]:
                bottom_left(eye_coords[0], eye_coords[1])
        elif eye_coords[0] > xRef[4]:
            if eye_coords[1] < yRef[4]:
                top_right(eye_coords[0], eye_coords[1])
            elif eye_coords[1] > yRef[4]:
                bottom_right(eye_coords[0], eye_coords[1])


# Middle Middle 0 0 4
def top_left(x, y):
    print("top left quadrant")
    xCoord = x * (xCal_points[0] / xRef[4])
    yCoord = y * (yCal_points[0] / yRef[4])
    print(f"Screen Coordinates: x:{xCoord}, y:{yCoord}")


# Middle Bottom 0 1 5
def bottom_left(x, y):
    print("bottom left quadrant")
    xCoord = x * (xCal_points[0] / xRef[5])
    yCoord = y * (yCal_points[1] / yRef[5])
    print(f"Screen Coordinates: x:{xCoord}, y:{yCoord}")


# Right Middle 1 0 7
def top_right(x, y):
    print("top right quadrant")
    xCoord = x * (xCal_points[1] / xRef[7])
    yCoord = y * (yCal_points[0] / yRef[7])
    print(f"Screen Coordinates: x:{xCoord}, y:{yCoord}")


# Right Bottom 1 1 8
def bottom_right(x, y):
    print("bottom right quadrant")
    xCoord = x * (xCal_points[1] / xRef[8])
    yCoord = y * (yCal_points[1] / yRef[8])
    print(f"Screen Coordinates: x:{xCoord}, y:{yCoord}")










