import PySpin
import sys

def reset_camera_to_default(cam):
    """Reset camera settings to factory defaults using Spinnaker API."""
    try:
        # Initialize the camera
        cam.Init()
        
        # Access the User Set selector node
        user_set_selector = PySpin.CEnumerationPtr(cam.GetNodeMap().GetNode("UserSetSelector"))
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
        user_set_load = PySpin.CCommandPtr(cam.GetNodeMap().GetNode("UserSetLoad"))
        if not PySpin.IsAvailable(user_set_load) or not PySpin.IsWritable(user_set_load):
            print("Unable to load UserSetLoad. Aborting reset.")
            return False
        user_set_load.Execute()
        
        print("Camera reset to default settings.")
        
        # Deinitialize the camera after resetting
        cam.DeInit()
        return True

    except PySpin.SpinnakerException as ex:
        print("Error resetting camera: %s" % ex)
        return False

def hard_reset():
    # Get the system instance
    system = PySpin.System.GetInstance()
    
    # Retrieve list of connected cameras
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    
    print("Number of cameras detected: %d" % num_cameras)

    # If no cameras are found, release system and exit
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        print("No cameras found!")
        sys.exit(1)

    # Iterate over all connected cameras
    for i, cam in enumerate(cam_list):
        print("Resetting camera %d to default settings..." % i)
        result = reset_camera_to_default(cam)
        if result:
            print("Camera %d reset successfully." % i)
        else:
            print("Failed to reset camera %d." % i)

    # Release the camera list and system instance
    del cam
    cam_list.Clear()
    system.ReleaseInstance()

