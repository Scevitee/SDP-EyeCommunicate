# import the InferencePipeline interface
from inference import InferencePipeline
# import a built in sink called render_boxes (sinks are the logic that happens after inference)
from inference.core.interfaces.stream.sinks import render_boxes

# create an inference pipeline object
pipeline = InferencePipeline.init(
    model_id="eye-tracking-2l0uc/5", # set the model id to a yolov8x model with in put size 1280
    # video_reference="your_video.mp4", # set the video reference (source of video), it can be a link/path to a video file, an RTSP stream url, or an integer representing a device id (usually 0 for built in webcams)
    video_reference=0,
    on_prediction=render_boxes, # tell the pipeline object what to do with each set of inference by passing a function
    api_key=API_KEY, # provide your roboflow api key for loading models from the roboflow api
)
# start the pipeline
pipeline.start()
# wait for the pipeline to finish
pipeline.join()
