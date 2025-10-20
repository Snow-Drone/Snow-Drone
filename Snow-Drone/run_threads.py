import threading
import time
import PySpin
from queue import Queue

from imaging.image_acquisition import CameraAcquisition
from imaging.image_processor import ImageProcessor
from weather_data.read_trisonica import DataLogger


def run_headless_mode(config, camera_acquisition_system, image_processing_system, data_logger):
    if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
        # Start the capture thread
        capture_thread = threading.Thread(target=camera_acquisition_system.capture, daemon=True)
        capture_thread.start()
        # Start image processing thread
        processing_tread = threading.Thread(target=image_processing_system.process_images, daemon=True)
        processing_tread.start()
        # Start the weather logging thread
        weather_logging_thread = threading.Thread(target=data_logger.log_data, daemon=True)
        weather_logging_thread.start()
        return True

    else:
        return False
    
    ## shouldnt get here
    return True

def run_live_mode(config, camera_acquisition_system, image_processing_system):
    if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
        # Start the capture thread
        capture_thread = threading.Thread(target=camera_acquisition_system.capture_live, daemon=True)
        capture_thread.start()
        # Start image processing thread
        processing_tread = threading.Thread(target=image_processing_system.process_images, daemon=True)
        processing_tread.start()
        return True

    else:
        return False
    
    ## shouldnt get here
    return True

def test_mode(config, camera_acquisition_system):
    n = 10 if (config["number"] == 0) else config["number"]
    print(f"Test flag enabled, acquiring {n} frames to $FOLDER: \n\nUsage help can be found with the --help flag.")
    try:
        if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
            camera_acquisition_system.capture(test=config["test"], n=n)
            camera_acquisition_system.close_camera()
        else:
            print("Failed to initialise camera")
            return False

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False
    return True
    # # Initialize camera
    # system = PySpin.System.GetInstance()
    # cam_list = system.GetCameras()
    # if cam_list.GetSize() == 0:
    #     print("No cameras detected. Exiting test mode.")
    #     return

    # camera = cam_list.GetByIndex(0)
    # camera.Init()

    # # Set camera parameters
    # camera.ExposureTime.SetValue(config["exposure_time"])
    # camera.Gain.SetValue(config["gain"])
    # camera.AcquisitionFrameRate.SetValue(config["frame_rate"])

    # # Start acquisition
    # camera.BeginAcquisition()
    # print(f"Capturing {config['number']} test images...")

    # for i in range(config["number"]):
    #     image_result = camera.GetNextImage()
    #     if image_result.IsIncomplete():
    #         print(f"Image incomplete with image status {image_result.GetImageStatus()}")
    #     else:
    #         print(f"Captured image {i + 1}: width = {image_result.GetWidth()}, height = {image_result.GetHeight()}")

    #     image_result.Release()

    # # End acquisition and clean up
    # camera.EndAcquisition()
    # camera.DeInit()
    # del camera
    # cam_list.Clear()
    # system.ReleaseInstance()
    # print("Test mode completed.")
    
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
        return True