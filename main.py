"""This is the main program and acts as the interplay between the image acquisition and the image processing."""

import argparse
import sys
from queue import Queue
import threading
import PySpin
import time

from image_acquisition import ImageAcquisition
from image_processor import ImageProcessor
from read_trisonica import DataLogger
from hard_reset import *


def parse_args():
    # Create Parser
    parser = argparse.ArgumentParser(prog="Snow-Drone", description="A simple script to capture and detect snowflakes for the snow drone project.")

    # Add arguments to parser
    parser.add_argument("-e", "--exposure_time", type=int, default=200, required=False) # Set default exposure time to 200 us
    parser.add_argument("-sd", "--strobe_duration", type=int, default=100, required=False) # Set default strobe duration to 100 us
    parser.add_argument("-stdel", "--strobe_delay", type=int, default=50, required=False) # Set default storbe delay to 50 us
    parser.add_argument("-g", "--gain", type=float, default=29.0, required=False) # Set default gain to the maximum value
    parser.add_argument("-f", "--frame_rate", type=float, default=10.0, required=False) # Set default frame rate to the max
    parser.add_argument("-q", "--queue_size", type=int, default=100, required=False) # Set default queue size to 50 images
    parser.add_argument("-set", "--sharp_edges_threshold", type=int, default=200, required=False) # Set default gradient threshold to 200 (empirical value)
    parser.add_argument("-T", "--test", action='store_true') # test mode, takes 10 pictures without processing them
    parser.add_argument("-n", "--number", type=int, default=0, required=False, help="Specify number of test images to be taken when in test mode. Is ignored in all other cases.")
    parser.add_argument("-l", "--live", action='store_true', help="Displays a live video of what the camera sees in a seperate window. Do not use while in headless mode.") # displays live feed of camera frames
    parser.add_argument("-y", "--reset", action='store_true')
    # parser.add_argument("--no-filter")
    parser.add_argument("-R", "--hard-reset", action='store_true', help='Runs the FLIR hard reset script for the drone camera and exits')
    parser.add_argument("-v", '--version', action='version', version='%(prog)s 0.1.3')

    # Parse Argumets
    args = parser.parse_args()

    # Convert argparse namespace to dictionary
    config = vars(args)

    return config

def stop_processes(camera_acquisition_system, capture_thread, image_queue, save_data):
    # Stop the image acquisition process
    print("\nStopping the process...")
    # Stop image acquisition
    camera_acquisition_system.stop_capture()
    # Wait until the image processor has processed all images from the queue
    while not image_queue.empty():
        time.sleep(0.5)
    # Stop the capture thread
    capture_thread.join()
    # Save the data in the image processor file
    save_data.set()
    time.sleep(0.5)
    # Stop the image queue
    image_queue.join()
    # Close the camera
    camera_acquisition_system.close_camera()

    print("Capturing stopped and camera closed. Exiting Program.")


def main():
    # Define camera configuration (settings)
    config = parse_args()

    # print(config)
    # return True

    if config["hard_reset"] == True:
        print("Performing a hard reset and exiting.")
        hard_reset()
        print("Sucessfully reset all cameras. Exiting now...")
        return True

    # if test flag isn't set, run acquisition loop
    # Initialize a queue to temporarily store images
    image_queue = Queue(maxsize=config["queue_size"])

    # Define a signal that tells the image processor to save the acquired data
    save_data = threading.Event()

    # Initialize the camera acquisition and image processing systems
    camera_acquisition_system = ImageAcquisition(config, image_queue)
    image_processing_system = ImageProcessor(config, image_queue, save_data)
    data_logger = DataLogger(save_data)

    if (not config["test"] == True) and (not config["live"] == True):
        # Start the process if the program is able to open the camera and configure its settings
        if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
            ## Using notation '_d' as these are daemon threads and '[...]_threadd' looks dumb
            # Start the capture thread
            capture_thread_d = threading.Thread(target=camera_acquisition_system.capture, daemon=True)
            capture_thread_d.start()
            # Start image processing thread
            processing_tread_d = threading.Thread(target=image_processing_system.process_images, daemon=True)
            processing_tread_d.start()
            # Start the weather logging thread
            weather_logging_thread_d = threading.Thread(target=data_logger.log_data, daemon=True)
            weather_logging_thread_d.start()

        else:
            return False

        # Contine the capturing process until an error appears or it is interrupted by the keyboard
        try:
            while True:
                time.sleep(0.05)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            stop_processes(camera_acquisition_system, capture_thread, image_queue, save_data)
            return False
        
        except KeyboardInterrupt:
            stop_processes(camera_acquisition_system, capture_thread, image_queue, save_data)

    elif config["live"] == True and not (config["test"] == True):
        # Start the process if the program is able to open the camera and configure its settings
        if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
            # Start the capture thread
            capture_thread = threading.Thread(target=camera_acquisition_system.capture_live, daemon=True)
            capture_thread.start()
            # Start image processing thread
            processing_tread = threading.Thread(target=image_processing_system.process_images, daemon=True)
            processing_tread.start()

        else:
            return False

        # Contine the capturing process until an error appears or it is interrupted by the keyboard
        try:
            while True:
                time.sleep(0.05)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            stop_processes(camera_acquisition_system, capture_thread, image_queue, save_data)
            return False
        
        except KeyboardInterrupt:
            stop_processes(camera_acquisition_system, capture_thread, image_queue, save_data)
    else:
        n = 10 if (config["number"] == 0) else config["number"]
        print(f"Test flag enabled, acquiring {n} frames to $FOLDER: \n\nUsage help can be found with the --help flag.")
        print("Beginning in 5 seconds...")
        print("5")
        time.sleep(1)
        print("4")
        time.sleep(1)
        print("3")
        time.sleep(1)
        print("2")
        time.sleep(1)
        print("1")
        time.sleep(1)
        print("GO!")
        try:
            if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
                camera_acquisition_system.capture(test=config["test"], n=n)
                camera_acquisition_system.close_camera()
            else:
                print("Failed to initialise camera")
                return False

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)

    print("Exiting...")
    return True


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
