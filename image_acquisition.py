"""This program will capture images and add them to the queue."""

import PySpin
import threading
import time
import os
import cv2
import numpy as np

class ImageAcquisition:
    def __init__(self, config, queue):
        self.config = config
        self.queue = queue

        # Create an Event to control the image capturing loop
        self.running = threading.Event()
        self.running.set()

    def open_camera(self):
        """Open and initialize the camera"""

        try:
            # Retrieve singleton reference to system object
            self.system = PySpin.System.GetInstance()

            # Get Camera
            self.cameras = self.system.GetCameras()

            # Return if there are no cameras
            if self.cameras.GetSize() == 0:
                # Clear camera list before releasing system
                self.cameras.Clear()

                # Release system instance
                self.system.ReleaseInstance()

                print('Not enough cameras!')
                input('Done! Press Enter to exit...')
                return False
            
            # Take the first camera from the list (assume there is only one camera)
            self.cam = self.cameras[0]

            # Initialize camera
            self.cam.Init()
        
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return True
    
    def camera_reset(self):
        try:
            # Access the User Set selector node
            user_set_selector = PySpin.CEnumerationPtr(self.cam.GetNodeMap().GetNode("UserSetSelector"))
            if not PySpin.IsAvailable(user_set_selector) or not PySpin.IsWritable(user_set_selector):
                print("Unable to access UserSetSelector. Aborting reset.")
                return False
            
            # Select the default user set
            user_set_default = user_set_selector.GetEntryByName("Default")
            if not PySpin.IsAvailable(user_set_default) or not PySpin.IsReadable(user_set_default):
                print("Default user set is not available. Aborting reset.")
                return False

            # Set the user set to default
            user_set_selector.SetIntValue(user_set_default.GetValue())

            # Load the default user set settings
            user_set_load = PySpin.CCommandPtr(self.cam.GetNodeMap().GetNode("UserSetLoad"))
            if not PySpin.IsAvailable(user_set_load) or not PySpin.IsWritable(user_set_load):
                print("Unable to load UserSetLoad. Aborting reset.")
                return False
            user_set_load.Execute()
            
            print("Camera reset to default settings.")

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False
        
        return True


    def setup_camera(self, reset=False):
        """Setup the camera and its parameters in order to start communicating with it."""

        try:
            # Give the user the option to reset the camera
            if  reset == False:
                user_input = input("Do you want to reset the camera? (yes/no): ")
                if user_input.lower() in ["yes", "y"]:
                    if self.camera_reset() == False:
                        return False
                    print("Camera successfully reset.")
            if reset == True:
                if self.camera_reset() == False:
                    return False
                print("Camera successfully reset.")
            
            # Retrieve GenICam nodemap
            self.nodemap = self.cam.GetNodeMap()

            # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
            node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsReadable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False

            # Set Acquisition mode to continuous
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsReadable(node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                return False
            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            # Set pixel format to monochrome 8
            self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
            
            # Check if automatic exposure an be disabled
            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic exposure. Aborting...')
                return False
            # Disable automatic exposure
            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

            # Check if exposure time can be changed
            if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
                print('Unable to set exposure time. Aborting...')
                return False 
            # Set the exposure time in microseconds while ensuring that the desired exposure time does not exceed the maximum
            exposure_time_to_set = min(self.cam.ExposureTime.GetMax(), self.config["exposure_time"])
            self.cam.ExposureTime.SetValue(exposure_time_to_set)

            # Check if automatic gain can be disabled
            if self.cam.GainAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic gain. Aborting...')
                return False
            # Disable automatic gain
            self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)

            # Check if gain can be changed
            if self.cam.Gain.GetAccessMode() != PySpin.RW:
                print('Unable to set gain. Aborting...')
                return False
            # Set the desired gain value (in dB) while ensuring that the desired gain does not exceed the maximum
            gain_to_set = min(self.config["gain"], self.cam.Gain.GetMax())
            self.cam.Gain.SetValue(gain_to_set)
            
            # Set Line Selector
            node_line_selector = PySpin.CEnumerationPtr(self.nodemap.GetNode('LineSelector'))
            if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsWritable(node_line_selector):
                print('\nUnable to set Line Selector (enumeration retrieval). Aborting...\n')
                return False
            
            # Change line selector to line 2
            entry_line_selector_line_2 = node_line_selector.GetEntryByName('Line2')
            if not PySpin.IsAvailable(entry_line_selector_line_2) or not PySpin.IsReadable(entry_line_selector_line_2):
                print('\nUnable to set Line Selector (entry retrieval). Aborting...\n')
                return False
            # Retrieve integer value from line selector
            line_selector_line_2 = entry_line_selector_line_2.GetValue()
            # Set integer value from line selector as new value
            node_line_selector.SetIntValue(line_selector_line_2)
            
            # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
            node_line_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('LineMode'))
            if not PySpin.IsAvailable(node_line_mode) or not PySpin.IsWritable(node_line_mode):
                print('\nUnable to set Line Mode (enumeration retrieval). Aborting...\n')
                return False

            # Set Line Mode to output
            entry_line_mode_output = node_line_mode.GetEntryByName('Output')
            if not PySpin.IsAvailable(entry_line_mode_output) or not PySpin.IsReadable(entry_line_mode_output):
                print('\nUnable to set Line Mode (entry retrieval). Aborting...\n')
                return False
            # Retrieve integer value from line mode
            line_mode_output = entry_line_mode_output.GetValue()
            # Set integer value from line mode as new value
            node_line_mode.SetIntValue(line_mode_output)
            
            # Set Line Source to AllPixel (or AnyPixel, Exposure Active)
            node_line_source = PySpin.CEnumerationPtr(self.nodemap.GetNode('LineSource'))
            if not PySpin.IsAvailable(node_line_source) or not PySpin.IsWritable(node_line_source):
                print('\nUnable to set Line Source (enumeration retrieval). Aborting...\n')
                return False

            entry_line_source_exposureactive = node_line_source.GetEntryByName('ExposureActive')
            if not PySpin.IsAvailable(entry_line_source_exposureactive) or not PySpin.IsReadable(entry_line_source_exposureactive):
                print('\nUnable to set Line Source to ExposureActive. Aborting...\n')
                return False
            # Retrieve integer value from line source
            line_source_exposureactive = entry_line_source_exposureactive.GetValue()
            # Set integer value from line source as new value
            node_line_source.SetIntValue(line_source_exposureactive)
            
            # Invert the line
            node_line_inverter = PySpin.CBooleanPtr(self.nodemap.GetNode('LineInverter'))
            if not PySpin.IsWritable(node_line_inverter):
                print('\nUnable to set Line Inverter (boolean retrieval). Aborting...\n')
                return False
            node_line_inverter.SetValue(True)
            
            # Set strobe delay in microseconds
            node_strobe_delay = PySpin.CFloatPtr(self.nodemap.GetNode('StrobeDelay'))
            if not PySpin.IsReadable(node_strobe_delay) or not PySpin.IsWritable(node_strobe_delay):
                print('\nUnable to set Strobe Delay (node retrieval). Aborting...\n')
                return False
            node_strobe_delay.SetValue(self.config["strobe_delay"])
            
            # Set strobe duration in microseconds
            node_strobe_duration = PySpin.CFloatPtr(self.nodemap.GetNode('StrobeDuration'))
            if not PySpin.IsReadable(node_strobe_duration) or not PySpin.IsWritable(node_strobe_duration):
                print('\nUnable to set Strobe Duration (node retrieval). Aborting...\n')
                return False
            node_strobe_duration.SetValue(self.config["strobe_duration"])

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False
        
        return True
        

    def capture(self, test=False, live=False):
        """Continuously capture images and add them to the queue"""

        print('\n*** START IMAGE ACQUISITION ***\n')

        # Begin Acquisition
        self.cam.BeginAcquisition()

        # Enable Acquisition frame rate control
        node_acquisition_frame_rate_control_enable = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnabled"))
        if not PySpin.IsAvailable(node_acquisition_frame_rate_control_enable) or not PySpin.IsWritable(node_acquisition_frame_rate_control_enable):
            print ('Unable to turn on Acquisition Frame Rate Control Enable (bool retrieval). Aborting...')
            return False
        node_acquisition_frame_rate_control_enable.SetValue(True)
        
        # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
        node_frame_rate_auto = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionFrameRateAuto"))
        if not PySpin.IsAvailable(node_frame_rate_auto) or not PySpin.IsWritable(node_frame_rate_auto):
            print('Unable to turn off Frame Rate Auto (enum retrieval). Aborting...')
            return False
        
        # Trun off automatic frame rate
        node_frame_rate_auto_off = node_frame_rate_auto.GetEntryByName("Off")
        if not PySpin.IsAvailable(node_frame_rate_auto_off) or not PySpin.IsReadable(node_frame_rate_auto_off):
            print ('Unable to set Frame Rate Auto to Off (entry retrieval). Aborting...')
            return False
        # Retrieve integer value from frame rate auto off
        frame_rate_auto_off = node_frame_rate_auto_off.GetValue()
        # Set integer value from frame rate auto off as new value
        node_frame_rate_auto.SetIntValue(frame_rate_auto_off)
        
        # Check if the acquisition frame rate mode can be accessed
        if self.cam.AcquisitionFrameRate.GetAccessMode() != PySpin.RW:
            print ('Unable to set Frame Rate. Aborting...')
            return False
        # Set the acquisition frame rate in Hertz ensuring that the desired exposure time does not exceed the maximum
        frame_rate = min(self.config["frame_rate"], self.cam.AcquisitionFrameRate.GetMax())
        self.cam.AcquisitionFrameRate.SetValue(frame_rate)

        # waiting time for image buffer and LED circuit to be ready (error otherwise)
        time.sleep(1)

        if (not test==True) and (live==False):
            # Running in normal operation 
            while self.running.is_set():
                # Capture image with a specified time-out value in miliseconds (time the program waits to get an image)
                image = self.cam.GetNextImage(int((1.0/frame_rate)*1500))
                if image.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image.GetImageStatus())
                elif not self.queue.full():
                    self.queue.put(image)
                    print("Captured image and added to queue.")
                    print(self.queue)
                else:
                    print("Queue is full. Skipping frame.")
                # Release image from buffer
                image.Release()

        elif (live==True) and (not test==True):
            while self.running.is_set():
                # Capture image with a specified time-out value in miliseconds (time the program waits to get an image)
                image = self.cam.GetNextImage(int((1.0/frame_rate)*1500))
                if image.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image.GetImageStatus())
                elif not self.queue.full():
                    self.queue.put(image)
                    print("Captured image and added to queue.")
                    print(self.queue)
                else:
                    print("Queue is full. Skipping frame.")
                
                image_array = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())
                frame = cv2.flip(image_array, 1)
                
                value = 20
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                lim = 255 - value
                v[v > lim] = 255
                v[v <= lim] += value
                final_hsv = cv2.merge((h, s, v))
                frame = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.equalizeHist(frame)

                # Custom window
                cv2.namedWindow('preview', cv2.WINDOW_KEEPRATIO)
                cv2.imshow('preview', frame)
                cv2.resizeWindow('preview', 500, 500)
                cv2.waitKey(1)

                # Release image from buffer
                image.Release()
        else:
            print("Running test acquisition...")
            #  Define the location of the folder to save the images 
            parent_dir="/home/orin/Snowscope/pictures_Test"

            # Make directory with name {Months-Days_Hours:Minutes:Seconds}
            current_time_tuple=time.localtime()
            directory = f"{current_time_tuple[1]}-{current_time_tuple[2]}_{current_time_tuple[3]}-{current_time_tuple[4]}-{current_time_tuple[5]}"
            path=os.path.join(parent_dir,directory)

            try:
                os.makedirs(path, exist_ok=True)
                print(f"Saving to {path}")

            except OSError as error:
                print("Error:", error)
                return False
            
            for i in range(10):
                # Capture image with a specified time-out value in miliseconds (time the program waits to get an image)
                image = self.cam.GetNextImage(int((1.0/frame_rate)*1500))
                if image.IsIncomplete():
                    print('Image incomplete with imasge status %d ...' % image.GetImageStatus())
                
                filename = os.path.join(path, f"Image_{i}.png")
                
                image_array = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())
                img = np.flipud(np.fliplr(image_array))

                cv2.imwrite(filename, img)
                image.Release()

    def capture_live(self):
        self.capture(test=False, live=True)

    def close_camera(self):
        """End acquisition, turn off LED and deinitialize the camera."""

        self.cam.EndAcquisition()
        
        # Turn off the LED
        node_line_source = PySpin.CEnumerationPtr(self.nodemap.GetNode('LineSource'))
        if PySpin.IsWritable(node_line_source):
            entry_line_source_user = node_line_source.GetEntryByName('UserOutput2')
            node_line_source.SetIntValue(entry_line_source_user.GetValue())
            print("LED turned off.")
        else:
            print("Unable to turn off LED.")

        # Deinitialize camera
        self.cam.DeInit()

        # Release reference to camera
        del self.cam

        # Clear camera list before releasing system
        self.cameras.Clear()

        # Release system instance
        self.system.ReleaseInstance()

    def stop_capture(self):
        """Stop the capture loop."""

        print("Stopping image capture...")
        self.running.clear()