# import the InferencePipeline interface
from inference import InferencePipeline
# import a built in sink called render_boxes (sinks are the logic that happens after inference)
from eyecoordinates import render_boxes_with_info
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values
# loading variables from .env file
load_dotenv()

# create an inference pipeline object
pipeline = InferencePipeline.init(
    model_id="eye-tracking-2l0uc/5",  # set the model id to a yolov8x model with in put size 1280
    video_reference=0,  # set the video reference (source of video), it can be a link/path to a video file, an RTSP stream url, or an integer representing a device id (usually 0 for built in webcams)
    on_prediction=render_boxes_with_info,  # Use the custom function to handle each set of inferences
    api_key=os.getenv("API_KEY"),  # provide your roboflow api key for loading models from the roboflow api
)

# start the pipeline
pipeline.start()

# wait for the pipeline to finish
pipeline.join()
