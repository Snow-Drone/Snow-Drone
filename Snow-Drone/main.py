"""This is the main program and acts as the interplay between the image acquisition and the image processing."""
import sys
import os
from queue import Queue
import threading
import PySpin
import time

import numpy as np
import torch
import cv2

from imaging.image_acquisition import ImageAcquisition
from imaging.image_preprocessor import ImagePreProcessor
from imaging.snowflake_processor import SnowflakeProcessor
from weather_data.read_trisonica import DataLogger

from run_threads import Runner

from utils.parser import parse_args
from utils.hard_reset import hard_reset
from utils.console_colours import info, warn, header, timef, queuef, err

def print_versions():
    print("Torch version:", torch.__version__)
    print("OpenCV version:", cv2.__version__)
    print("NumPy version:", np.__version__)
    print("Torch CUDA available:", torch.cuda.is_available())

def main():
    # Define camera configuration (settings)
    config = parse_args()

    if config["hard_reset"] == True:
        info("Performing a hard reset and exiting.")
        hard_reset()
        return True
    
    print_versions()

    # if test flag isn't set, run acquisition loop
    # Initialize a queue to temporarily store images and a threading event to signal when to save data
    raw_image_queue = Queue(maxsize=config["queue_size"])
    processing_queue = Queue(maxsize=config["queue_size"])
    save_data = threading.Event()

    # Initialize the camera acquisition and image processing systems
    camera_acquisition_system = ImageAcquisition(config, raw_image_queue)
    if not config["test"]:
        image_processing_system = ImagePreProcessor(config, raw_image_queue, processing_queue, save_data)
        snowflake_processing_system = SnowflakeProcessor(config, processing_queue, save_data)
    runner = Runner()
    
    data = False
    if os.path.exists("/dev/ttyUSB0"):
        print("[INFO] Anemometer detected, starting logger...")
        data_logger = DataLogger(save_data)
        data = True
    
    ## Main program logic
    
    if config["test"] == True:
        # Run in test mode (is allowed to run with live flag as well)
        success = runner.test_mode(config, camera_acquisition_system)
        if not success:
            return False
        
    elif config["live"] == True and not (config["test"] == True):
        # Run in live mode
        success = runner.run_live_mode(config, camera_acquisition_system, image_processing_system, snowflake_processing_system)
        if not success:
            return False
        # Contine the capturing process until an error appears or it is interrupted by the keyboard
        try:
            while True:
                time.sleep(0.05)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            runner.stop_processes(camera_acquisition_system, raw_image_queue, processing_queue, save_data)
            return False
        
        except KeyboardInterrupt:
            runner.stop_processes(camera_acquisition_system, raw_image_queue, processing_queue, save_data)
            
    else:
        # Run in headless mode
        if not data and not config["headless_no_anemometer"]:
            print("[ERROR]: Can't run in headless mode without anemometer attached. Aborting...")
            return False
        if config["headless_no_anemometer"]:
            success = runner.run_headless_mode_no_anemometer(config, camera_acquisition_system, image_processing_system, snowflake_processing_system)
        else:
            success = runner.run_headless_mode(config, camera_acquisition_system, image_processing_system, snowflake_processing_system, data_logger)
        if not success:
            return False
        # Contine the capturing process until an error appears or it is interrupted by the keyboard
        try:
            while True:
                time.sleep(0.05)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            runner.stop_processes(camera_acquisition_system, raw_image_queue, processing_queue, save_data)
            return False
        
        except KeyboardInterrupt:
            runner.stop_processes(camera_acquisition_system, raw_image_queue, processing_queue, save_data)
            
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
