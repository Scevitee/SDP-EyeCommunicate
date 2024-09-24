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

DEFAULT_BBOX_ANNOTATOR = sv.BoundingBoxAnnotator()
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
        # Loop through predictions and print prediction info to terminal
        if isinstance(frame_prediction, dict) and 'predictions' in frame_prediction:
            for prediction in frame_prediction['predictions']:
                x = prediction.get("x", 0)
                y = prediction.get("y", 0)
                width = prediction.get("width", 0)
                height = prediction.get("height", 0)
                confidence = prediction.get("confidence", 0)
                class_name = prediction.get("class", "unknown")
                
                # Print details to terminal
                print(f"Class: {class_name}, Confidence: {confidence:.2f}, (x: {x}, y: {y}, width: {width}, height: {height})")
                
        # End of modified code
        images.append((idx, image))
    if sequential_input_provided:
        on_frame_rendered((video_frame[0].source_id, images[0][1]))
    else:
        on_frame_rendered(images)
