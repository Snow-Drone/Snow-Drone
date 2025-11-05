#!/bin/bash

# Reset Camera
python3 Snow-Drone/main.py --hard-reset
# Needs to be done twice because of a bug in the camera driver
python3 Snow-Drone/main.py --hard-reset

# Start the main program
python3 Snow-Drone/main.py -y -f 20

### End of run.sh
# To run without anemometer enabled, use the following command instead:
# python3 Snow-Drone/main.py -y --headless-no-anemometer