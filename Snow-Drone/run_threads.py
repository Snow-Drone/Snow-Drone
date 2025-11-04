import threading
import time
import PySpin


class Runner:
    def __init__(self):
        pass        

    def run_headless_mode(self, config, camera_acquisition_system, image_conversion_system, image_processing_system, image_filtering_system, snowflake_processing_system, data_logger):
        if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
            # Start the capture thread
            self.captured = threading.Thread(target=camera_acquisition_system.capture, daemon=True)
            self.captured.start()
            # Start image conversion thread
            self.conversiond = threading.Thread(target=image_conversion_system.convert, daemon=True)
            self.conversiond.start()
            # Start image processing thread
            self.processingd = threading.Thread(target=image_processing_system.process_images, daemon=True)
            self.processingd.start()
            # Start the filtering thread
            self.filterd = threading.Thread(target=image_filtering_system.filter_images, daemon=True)
            self.filterd.start()
            # Start snowflake processing thread
            self.snowflaked = threading.Thread(target=snowflake_processing_system.process_snowflakes, daemon=True)
            self.snowflaked.start()
            # Start the weather logging thread
            self.weather_logging_thread = threading.Thread(target=data_logger.log_data, daemon=True)
            self.weather_logging_thread.start()
            return True

        else:
            return False
        ## shouldnt get here
        return True
    
    def run_headless_mode_no_anemometer(self, config, camera_acquisition_system, image_conversion_system, image_processing_system, image_filtering_system, snowflake_processing_system):
        if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
            # Start the capture thread
            self.captured = threading.Thread(target=camera_acquisition_system.capture, daemon=True)
            self.captured.start()
            # Start image conversion thread
            self.conversiond = threading.Thread(target=image_conversion_system.convert, daemon=True)
            self.conversiond.start()
            # Start image processing thread
            self.processingd = threading.Thread(target=image_processing_system.process_images, daemon=True)
            self.processingd.start()
            # Start the filtering thread
            self.filterd = threading.Thread(target=image_filtering_system.filter_images, daemon=True)
            self.filterd.start()
            # Start snowflake processing thread
            self.snowflaked = threading.Thread(target=snowflake_processing_system.process_snowflakes, daemon=True)
            self.snowflaked.start()
            return True

        else:
            return False
        ## shouldnt get here
        return True

    def run_live_mode(self, config, camera_acquisition_system, image_conversion_system, image_processing_system, image_filtering_system, snowflake_processing_system):
        if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
            # Start the capture thread
            self.captured = threading.Thread(target=camera_acquisition_system.capture_live, daemon=True)
            self.captured.start()
            # Start image conversion thread
            self.conversiond = threading.Thread(target=image_conversion_system.convert, daemon=True)
            self.conversiond.start()
            # Start image processing thread
            self.processingd = threading.Thread(target=image_processing_system.process_images, daemon=True)
            self.processingd.start()
            # Start the filtering thread
            self.filterd = threading.Thread(target=image_filtering_system.filter_images, daemon=True)
            self.filterd.start()
            # Start snowflake processing thread
            self.snowflaked = threading.Thread(target=snowflake_processing_system.process_snowflakes, daemon=True)
            self.snowflaked.start()
            return True

        else:
            return False
        
        ## shouldnt get here
        return True

    def test_mode(self, config, camera_acquisition_system):
        n = 10 if (config["number"] == 0) else config["number"]
        print(f"Test flag enabled, acquiring {n} frames to $FOLDER: \n\nUsage help can be found with the --help flag.")
        try:
            if camera_acquisition_system.open_camera() and camera_acquisition_system.setup_camera(config["reset"]):
                camera_acquisition_system.test_capture(n=n, show=config["live"])
                camera_acquisition_system.close_camera()
            else:
                print("Failed to initialise camera")
                return False

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False
        return True
        
    def stop_processes(self, camera_acquisition_system, image_raw_queue, image_in_queue, image_out_queue, snowflake_queue, save_data):
        # Stop the image acquisition process
        print("\nStopping the process...")
        # Stop image acquisition
        camera_acquisition_system.stop_capture()
        # Wait until the image processor has processed all images from the queue
        while not image_raw_queue.empty():
            time.sleep(0.5)
        while not image_in_queue.empty():
            time.sleep(0.5)
        while not image_out_queue.empty():
            time.sleep(0.5)
        while not snowflake_queue.empty():
            time.sleep(0.5)

        # Stop the capture thread
        self.captured.join()
        # Save the data in the image processor file
        save_data.set()
        time.sleep(0.5)
        # Stop the image queue
        image_raw_queue.join()
        image_in_queue.join()
        image_out_queue.join()
        snowflake_queue.join()
        # Wait for the processing threads to finish
        self.conversiond.join()
        self.processingd.join()
        self.snowflaked.join()
        self.filterd.join()
        # Close the camera
        camera_acquisition_system.close_camera()

        print("Capturing stopped and camera closed. Exiting Program.")
        return True