"""This is the main program and acts as the interplay between the image acquisition and the image processing."""

import argparse
import sys
from queue import Queue
import threading
import PySpin
import time

from image_acquisition import ImageAcquisition
from image_processor import ImageProcessor


def parse_args():
    # Create Parser
    parser = argparse.ArgumentParser()

    # Add arguments to parser
    parser.add_argument("-e", "--exposure_time", type=int, default=200, required=False) # Set default exposure time to 200 us
    parser.add_argument("-sd", "--strobe_duration", type=int, default=100, required=False) # Set default strobe duration to 100 us
    parser.add_argument("-stdel", "--strobe_delay", type=int, default=50, required=False) # Set default storbe delay to 50 us
    parser.add_argument("-g", "--gain", type=float, default=30.0, required=False) # Set default gain to the maximum value
    parser.add_argument("-f", "--frame_rate", type=float, default=10.0, required=False) # Set default frame rate to the max
    parser.add_argument("-q", "--queue_size", type=int, default=100, required=False) # Set default queue size to 50 images
    parser.add_argument("-set", "--sharp_edges_threshold", type=int, default=300, required=False) # Set default gradient threshold to 300 (empirical value)

    # Parse Argumets
    args = parser.parse_args()

    # Convert argparse namespace to dictionary
    config = vars(args)

    return config

def stop_processes(camera_acquisition_system, capture_thread, image_queue):
    # Stop the image acquisition process
    print("\nStopping the process...")
    # Stop image acquisition
    camera_acquisition_system.stop_capture()
    # Wait until the image processor has processed all images from the queue
    while not image_queue.empty():
        time.sleep(0.5)
    # Stop the capture thread
    capture_thread.join()
    # Stop the image queue
    image_queue.join()
    # Close the camera
    camera_acquisition_system.close_camera()

    print("Capturing stopped and camera closed. Exiting Program.")


def main():
    # Define camera configuration (settings)
    config = parse_args()
    
    # Initialize a queue to temporarily store images
    image_queue = Queue(maxsize=config["queue_size"]) # Adjust size as needed

    # Initialize the camera acquisition and image processing systems
    camera_acquisition_system = ImageAcquisition(config, image_queue)
    image_processing_system = ImageProcessor(config, image_queue)

    # Start the process if the program is able to open the camera and configure its settings
    if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera():
        # Start the capture thread
        capture_thread = threading.Thread(target=camera_acquisition_system.capture, daemon=True)
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
        stop_processes(camera_acquisition_system, capture_thread, image_queue)
        return False
    
    except KeyboardInterrupt:
        stop_processes(camera_acquisition_system, capture_thread, image_queue)

    return True


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
