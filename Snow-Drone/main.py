"""This is the main program and acts as the interplay between the image acquisition and the image processing."""
import sys
from queue import Queue
import threading
import PySpin
import time

from imaging.image_acquisition import ImageAcquisition
from imaging.image_processor import ImageProcessor
from weather_data.read_trisonica import DataLogger
from utils.parse_args import parse_args
from utils.hard_reset_cameras import hard_reset

from run_threads import run_headless_mode, run_live_mode, test_mode, stop_processes

def main():
    # Define camera configuration (settings)
    config = parse_args()

    if config["hard_reset"] == True:
        print("Performing a hard reset and exiting.")
        hard_reset()
        print("Sucessfully reset all cameras. Exiting now...")
        return True

    # if test flag isn't set, run acquisition loop
    # Initialize a queue to temporarily store images and a threading event to signal when to save data
    image_queue = Queue(maxsize=config["queue_size"])
    save_data = threading.Event()

    # Initialize the camera acquisition and image processing systems
    camera_acquisition_system = ImageAcquisition(config, image_queue)
    image_processing_system = ImageProcessor(config, image_queue, save_data)
    data_logger = DataLogger(save_data)
    
    ## Main program logic
    if config["test"] == True and config["live"] == True:
        print("Error: Cannot run in both test mode and live mode simultaneously. Please choose one mode.")
        return False
    
    if config["test"] == True:
        # Run in test mode
        success = test_mode(config, camera_acquisition_system)
        if not success:
            return False
        
    elif config["live"] == True and not (config["test"] == True):
        # Run in live mode
        success = run_live_mode(config, camera_acquisition_system, image_processing_system)
        if not success:
            return False
        # Contine the capturing process until an error appears or it is interrupted by the keyboard
        try:
            while True:
                time.sleep(0.05)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            stop_processes(camera_acquisition_system, image_queue, save_data)
            return False
        
        except KeyboardInterrupt:
            stop_processes(camera_acquisition_system, image_queue, save_data)
            
    else:
        # Run in headless mode
        success = run_headless_mode(config, camera_acquisition_system, image_processing_system, data_logger)
        if not success:
            return False
        # Contine the capturing process until an error appears or it is interrupted by the keyboard
        try:
            while True:
                time.sleep(0.05)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            stop_processes(camera_acquisition_system, image_queue, save_data)
            return False
        
        except KeyboardInterrupt:
            stop_processes(camera_acquisition_system, image_queue, save_data)

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
