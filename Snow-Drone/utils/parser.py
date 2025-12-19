import argparse

def parse_args():
    # Create Parser
    parser = argparse.ArgumentParser(prog="Snow-Drone", description="A simple script to capture and detect snowflakes for the snow drone project.")

    # Add arguments to parser
    parser.add_argument("-e", "--exposure_time", type=int, default=390, required=False) # Set default exposure time to 300 us. This yields effective exposure time of 150 us.
    parser.add_argument("-sd", "--strobe_duration", type=int, default=400, required=False) # Set default strobe duration to 300 us
    parser.add_argument("-stdel", "--strobe_delay", type=int, default=0, required=False) # Set default storbe delay to 0 us
    parser.add_argument("-g", "--gain", type=float, default=29.0, required=False) # Set default gain to the maximum value
    parser.add_argument("-f", "--frame_rate", type=float, default=10.0, required=False) # Set default frame rate to the max
    parser.add_argument("-q", "--queue_size", type=int, default=100, required=False) # Set default queue size to 50 images
    parser.add_argument("-set", "--sharp_edges_threshold", type=int, default=100, required=False) # Set default gradient threshold to 200 (empirical value)
    parser.add_argument("-T", "--test", action='store_true') # test mode, takes 10 pictures without processing them
    parser.add_argument("-n", "--number", type=int, default=0, required=False, help="Specify number of test images to be taken when in test mode. Is ignored in all other cases.")
    parser.add_argument("-l", "--live", action='store_true', help="Displays a live video of what the camera sees in a seperate window. Do not use while in headless mode.") # displays live feed of camera frames

    parser.add_argument("-y", "--reset", action='store_true')
    parser.add_argument("--headless-no-anemometer", action='store_true', help="Allows user to run headless mode when no anemometer is attatched. Generally used for testing.")
    # parser.add_argument("--no-filter")
    parser.add_argument('-ws', "--server", action='store_true', help="Enables local web server to host images.")
    def positive_int(x):
        try:
            v = int(x)
        except Exception:
            raise argparse.ArgumentTypeError('must be an integer')
        if v <= 0:
            raise argparse.ArgumentTypeError('ring_size must be a positive integer')
        return v
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', default=5000, type=int)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--ring-size', type=positive_int, default=10,
                        help='Size of the in-memory ring buffer for images')
    
    parser.add_argument("-R", "--hard-reset", action='store_true', help='Runs the FLIR hard reset script for the drone camera and exits')
    parser.add_argument("-v", '--version', action='version', version='%(prog)s 0.1.4')

    # Parse Argumets
    args = parser.parse_args()

    # Convert argparse namespace to dictionary
    config = vars(args)

    return config