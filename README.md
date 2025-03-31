# FLIR Grasshopper3 Image Capture

## Overview
This repository contains Python code for capturing images using a **FLIR Grasshopper3 GS3-U3-23S6M** camera. The system continuously captures images, processes them, and detects snowflakes. If a snowflake is identified, the image is saved; otherwise, it is discarded from the queue.

## How It Works
1. **Execution:** Run `main.py` to start the image capture process.
2. **Image Acquisition:** The `image_acquisition.py` script interacts with the camera and continuously captures images.
3. **Queue Processing:** Captured images are added to a queue for analysis.
4. **Image Processing:** The `image_processor.py` script analyzes each image in the queue. If a snowflake is detected, the image is saved.
5. **Removal from Queue:** The image is removed from the queue after image processing.

## Requirements
Ensure you have the necessary dependencies installed before running the scripts. You may need the following Python packages:
```bash
pip install opencv-python numpy flirpy
```

## Usage
To start the image capture and processing, run:
```bash
python3 main.py
```

## Parameters
The following camera parameters can be changed by a command in the terminal at the start of the program. 
1. **Exposure Time**
2. **Strobe Duration**
3. **Strobe Delay**
4. **Gain/ISO**
5. **Frame Rate**
6. **Queue Size**\
An example is written below, which changes the exposure time to 150 microseconds:
```bash
python3 main.py --exposure_time 150
```

## Author
Léon Mamié - Master Student at IFD (ETH Zürich)

