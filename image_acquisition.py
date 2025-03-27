"""This program will capture images and add them to the queue."""

import PySpin
import threading
import time

class ImageAcquisition:
    def __init__(self, config, queue):
        self.config = config
        self.queue = queue

        # Create an Event to control the image capturing loop
        self.running = threading.Event()
        self.running.set()

    def open_camera(self):
        """Open and initialize the camera"""

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

        return True


    def set_camera_settings(self):
        """Set the steam mode to be able to send commands to the camera"""

        try:
            # Retrieve GenICam nodemap
            self.nodemap = self.cam.GetNodeMap()

            # Retrieve Stream nodemap
            nodemap_tlstream = self.cam.GetTLStreamNodeMap()

            # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
            node_stream_mode = PySpin.CEnumerationPtr(nodemap_tlstream.GetNode('StreamMode'))

            # Access reading and writing stream mode of node
            PySpin.IsReadable(node_stream_mode)
            PySpin.IsWritable(node_stream_mode)

            # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
            node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsReadable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False

            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsReadable(node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                return False

            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            print('Acquisition mode set to continuous...')

            # Set pixel format to monochrome 8
            self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
            
            # Set exposure time
            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic exposure. Aborting...')
                return False

            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            print('Automatic exposure disabled...')


            if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
                print('Unable to set exposure time. Aborting...')
                return False
            
            # Set the exposure time in microseconds
            # Ensure desired exposure time does not exceed the maximum
            exposure_time_to_set = min(self.cam.ExposureTime.GetMax(), self.config["exposure_time"])
            self.cam.ExposureTime.SetValue(exposure_time_to_set)
            print('Shutter time set to %s microseconds.\n' % exposure_time_to_set)

            # Disable automatic gain, if available
            if self.cam.GainAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic gain. Aborting...')
                return False

            self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            print('Automatic gain disabled...')

            # Check if Gain is available and writable
            if self.cam.Gain.GetAccessMode() != PySpin.RW:
                print('Unable to set gain. Aborting...')
                return False

            # Set the desired gain value (in dB)
            gain_to_set = min(self.config["gain"], self.cam.Gain.GetMax())
            self.cam.Gain.SetValue(gain_to_set)
            print('Gain set to {} dB...'.format(gain_to_set))

            
            # Set Line Selector
            node_line_selector = PySpin.CEnumerationPtr(self.nodemap.GetNode('LineSelector'))
            if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsWritable(node_line_selector):
                print('\nUnable to set Line Selector (enumeration retrieval). Aborting...\n')
                return False
            
            # Configure Line2 
            entry_line_selector_line_2 = node_line_selector.GetEntryByName('Line2')
            if not PySpin.IsAvailable(entry_line_selector_line_2) or not PySpin.IsReadable(entry_line_selector_line_2):
                print('\nUnable to set Line Selector (entry retrieval). Aborting...\n')
                return False
            
            line_selector_line_2 = entry_line_selector_line_2.GetValue()

            node_line_selector.SetIntValue(line_selector_line_2)
            
            # Set Line Mode to output
            node_line_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('LineMode'))
            if not PySpin.IsAvailable(node_line_mode) or not PySpin.IsWritable(node_line_mode):
                print('\nUnable to set Line Mode (enumeration retrieval). Aborting...\n')
                return False

            entry_line_mode_output = node_line_mode.GetEntryByName('Output')
            if not PySpin.IsAvailable(entry_line_mode_output) or not PySpin.IsReadable(entry_line_mode_output):
                print('\nUnable to set Line Mode (entry retrieval). Aborting...\n')
                return False

            line_mode_output = entry_line_mode_output.GetValue()

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

            line_source_exposureactive = entry_line_source_exposureactive.GetValue()

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

            print('Strobe Delay set to {0:.0f} microseconds.'.format(node_strobe_delay.GetValue()))
            
            # Set strobe duration in microseconds
            node_strobe_duration = PySpin.CFloatPtr(self.nodemap.GetNode('StrobeDuration'))
            if not PySpin.IsReadable(node_strobe_duration) or not PySpin.IsWritable(node_strobe_duration):
                print('\nUnable to set Strobe Duration (node retrieval). Aborting...\n')
                return False

            node_strobe_duration.SetValue(self.config["strobe_duration"])

            print('Strobe Duration set to {0:.0f} microseconds.'.format(node_strobe_duration.GetValue()))

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False
        
        return True
        

    def close_camera(self):
        """End acquisition, turn off LED and deinitialize the camera"""

        self.cam.EndAcquisition()
        
        ### Turn off the LED
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

    def capture(self):
        """Continously capture images and add them to the queue"""

        print('*** IMAGE ACQUISITION ***\n')

        # Begin Acquisition
        self.cam.BeginAcquisition()

        ### Enable AcquisitionFrameRateControlEnable ###
        node_acquisition_frame_rate_control_enable = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnabled"))
        if not PySpin.IsAvailable(node_acquisition_frame_rate_control_enable) or not PySpin.IsWritable(node_acquisition_frame_rate_control_enable):
            print ('Unable to turn on Acquisition Frame Rate Control Enable (bool retrieval). Aborting...')
            return False
        
        node_acquisition_frame_rate_control_enable.SetValue(True)
        
        ### Disable FrameRateAuto ###
        node_frame_rate_auto = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionFrameRateAuto"))
        if not PySpin.IsAvailable(node_frame_rate_auto) or not PySpin.IsWritable(node_frame_rate_auto):
            print('Unable to turn off Frame Rate Auto (enum retrieval). Aborting...')
            return False
        
        node_frame_rate_auto_off = node_frame_rate_auto.GetEntryByName("Off")
        if not PySpin.IsAvailable(node_frame_rate_auto_off) or not PySpin.IsReadable(node_frame_rate_auto_off):
            print ('Unable to set Frame Rate Auto to Off (entry retrieval). Aborting...')
            return False
        
        frame_rate_auto_off = node_frame_rate_auto_off.GetValue()
        
        node_frame_rate_auto.SetIntValue(frame_rate_auto_off)
        
        
        ### Set AcquisitionFrameRate in Hertz
        if self.cam.AcquisitionFrameRate.GetAccessMode() != PySpin.RW:
            print ('Unable to set Frame Rate. Aborting...')
            return False
        
        self.cam.AcquisitionFrameRate.SetValue(self.config["frame_rate"])
        max_frame_rate = self.cam.AcquisitionFrameRate.GetMax()
        print(f"Mamimum possible acquisiton frame rate: {max_frame_rate} Hz")

        # waiting time for buffer to be ready (error otherwise)
        time.sleep(1)
        
        print ('Frame Rate is set to %.2f Hertz.' % self.cam.AcquisitionFrameRate.GetValue())

        while self.running.is_set():
            # Capture image
            image = self.cam.GetNextImage(int((1.0/self.config["frame_rate"])*1500))
            if image.IsIncomplete():
                print('Image incomplete with image status %d ...' % image.GetImageStatus())
            elif not self.queue.full():
                self.queue.put(image)
                print("Captured and added to queue:", image)
                print(self.queue)
            else:
                print("Queue is full. Skipping frame.")
            # Release image from buffer
            image.Release()

    def stop_capture(self):
        """Stop the capture loop."""

        print("Stopping image capture...")
        self.running.clear()