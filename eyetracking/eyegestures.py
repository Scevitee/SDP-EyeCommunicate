
from eyeGestures.gazeEstimator import GazeTracker
import eyeGestures.screenTracker.dataPoints as dp
from eyeGestures.calibration_v1 import Calibrator as Calibrator_v1
from eyeGestures.calibration_v2 import Calibrator as Calibrator_v2, CalibrationMatrix, euclidean_distance
from eyeGestures.gevent import Gevent, Cevent
from eyeGestures.utils import timeit, Buffor
import numpy as np
import pickle
import cv2

import random

VERSION = "2.0.0"

class EyeGestures_v2:
    """Main class for EyeGesture tracker. It configures and manages entire algorithm"""

    def __init__(self, calibration_radius = 1000):
        self.monitor_width  = 1
        self.monitor_height = 1
        self.calibration_radius = calibration_radius

        self.clb = dict() # Calibrator_v2()
        self.cap = None
        self.gestures = EyeGestures_v1(285,115,200,100)

        self.calibration = dict()

        self.CN = 5

        self.average_points = dict()
        self.iterator = dict()
        self.filled_points= dict()
        self.enable_CN = False
        self.calibrate_gestures = False

        self.fix = 0.8

    def saveModel(self, context = "main"):
        if context in self.clb:
            return pickle.dumps(self.clb[context])

    def loadModel(self,model, context = "main"):
        self.clb[context] = pickle.loads(model)

    def uploadCalibrationMap(self,points,context = "main"):
        self.addContext(context)
        self.clb[context].updMatrix(np.array(points))

    def getLandmarks(self, frame, calibrate = False, context="main"):

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame,1)
        # frame = cv2.resize(frame, (360, 640))

        event, cevent = self.gestures.step(
            frame,
            context,
            calibrate, # set calibration - switch to False to stop calibration
            self.monitor_width,
            self.monitor_height,
            0, 0, self.fix, 100)

        if event is not None or cevent is not None:
            cursor_x, cursor_y = event.point[0],event.point[1]
            l_eye_landmarks = event.l_eye.getLandmarks()
            r_eye_landmarks = event.r_eye.getLandmarks()

            cursors = np.array([cursor_x,cursor_y]).reshape(1, 2)
            eye_events = np.array([event.blink,event.fixation]).reshape(1, 2)
            key_points = np.concatenate((cursors,l_eye_landmarks,r_eye_landmarks,eye_events))
            return np.array((cursor_x, cursor_y)), key_points, event.blink, event.fixation, cevent
        return np.array((0.0, 0.0)), np.array([]), 0, 0, None

    def setClassicImpact(self,impact):
        self.CN = impact

    def reset(self, context = "main"):
        self.filled_points[context] = 0
        if context in self.clb:
           self.addContext(context)

    def setFixation(self,fix):
        self.fix = fix

    def setClassicalImpact(self,CN):
        self.CN = CN

    def enableCNCalib(self):
        self.enable_CN = True

    def disableCNCalib(self):
        self.enable_CN = False

    def addContext(self, context):
        if context not in self.clb:
            self.clb[context] = Calibrator_v2(self.calibration_radius)
            self.average_points[context] = Buffor(20)
            self.iterator[context] = 0
            self.average_points[context] = np.zeros((20,2))
            self.filled_points[context] = 0
            self.calibration[context] = False


    def step(self, frame, calibration, width, height, context="main"):
        self.addContext(context)

        self.calibration[context] = calibration
        self.monitor_width = width
        self.monitor_height = height

        classic_point, key_points, blink, fixation, cevent = self.getLandmarks(frame,
                                                                               self.calibrate_gestures and self.enable_CN,
                                                                               context = context)

        if cevent is None:
            return (None, None)

        margin = 10
        if (classic_point[0] <= margin) and self.calibration[context]:
            self.calibrate_gestures = cevent.calibration
        elif (classic_point[0] >= width - margin) and self.calibration[context]:
            self.calibrate_gestures = cevent.calibration
        elif (cevent.point[1] <= margin) and self.calibration[context]:
            self.calibrate_gestures = cevent.calibration
        elif (classic_point[1] >= height - margin) and self.calibration[context]:
            self.calibrate_gestures = cevent.calibration
        else:
            self.calibrate_gestures = False

        y_point = self.clb[context].predict(key_points)
        self.average_points[context][1:,:] = self.average_points[context][:(self.average_points[context].shape[0] - 1),:]
        if fixation <= self.fix:
            self.average_points[context][0,:] = y_point

        if self.filled_points[context] < self.average_points[context].shape[0] and (y_point != np.array([0.0,0.0])).any():
            self.filled_points[context] += 1

        averaged_point = (np.sum(self.average_points[context][:,:],axis=0) + (classic_point * self.CN))/(self.filled_points[context] + self.CN)

        if self.calibration[context] and (self.clb[context].insideClbRadius(averaged_point,width,height) or self.filled_points[context] < self.average_points[context].shape[0] * 10):
            self.clb[context].add(key_points,self.clb[context].getCurrentPoint(width,height))

        if self.calibration[context] and self.clb[context].insideAcptcRadius(averaged_point,width,height):
            self.iterator[context] += 1
            if self.iterator[context] > 10:
                self.iterator[context] = 0
                self.clb[context].movePoint()
                # self.clb[context].increase_precision()

        gevent = Gevent(averaged_point,blink,fixation)
        cevent = Cevent(self.clb[context].getCurrentPoint(width,height),self.clb[context].acceptance_radius, self.clb[context].calibration_radius)
        return (gevent, cevent)

class EyeGestures_v1:
    """Main class for EyeGesture tracker. It configures and manages entier algorithm"""

    def __init__(self,
                 roi_x=225,
                 roi_y=105,
                 roi_width=80,
                 roi_height=15):

        screen_width = 500
        screen_height = 500
        height = 250
        width = 250

        roi_x = roi_x % screen_width
        roi_y = roi_y % screen_height
        roi_width = roi_width % screen_width
        roi_height = roi_height % screen_height

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.screen = dp.Screen(
            screen_width,
            screen_height)

        self.gaze = GazeTracker(screen_width,
                                screen_height,
                                width,
                                height,
                                roi_x,
                                roi_y,
                                roi_width,
                                roi_height)

        self.calibrators = dict()
        self.calibrate = False

    def getFeatures(self, image):
        """[NOT RECOMMENDED] Function allowing for extraction of gaze features from image"""

        return self.gaze.getFeatures(image)

    # @timeit
    # 0.011 - 0.015 s for execution
    def step(self, image,
                 context,
                 calibration,
                 display_width,
                 display_height,
                 display_offset_x=0,
                 display_offset_y=0,
                 fixation_freeze=0.7,
                 freeze_radius=20,
                 offset_x=0,
                 offset_y=0):
        """Function performing estimation and returning event object"""

        display = dp.Display(
            display_width,
            display_height,
            display_offset_x,
            display_offset_y
        )

        # allow for random recalibration shot
        event = self.gaze.estimate(image,
                                  display,
                                  context,
                                  calibration,
                                  fixation_freeze,
                                  freeze_radius,
                                  offset_x,
                                  offset_y)
        cevent = None

        if event is not None:
            cursor_x,cursor_y = event.point[0],event.point[1]
            if context in self.calibrators:
                self.calibrate = self.calibrators[context].calibrate(cursor_x,cursor_y,event.fixation)
            else:
                self.calibrators[context] = Calibrator_v1(display_width,display_height,cursor_x,cursor_y)
                self.calibrate = self.calibrators[context].calibrate(cursor_x,cursor_y,event.fixation)

            cpoint = self.calibrators[context].get_current_point()
            calibration = self.calibrate and cpoint != (0,0)
            cevent = Cevent(cpoint,100, 100, calibration)

        return (event, cevent)