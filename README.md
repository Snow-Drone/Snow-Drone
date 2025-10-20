# Snow-Drone: FLIR Grasshopper3 Image Capture

## Overview
This repository contains Python code for capturing images using a **FLIR Grasshopper3 GS3-U3-23S6M** camera. The system continuously captures images into a queue, processes them, and detects snowflakes. If a snowflake is identified, the image is saved; otherwise, it is discarded from the queue.

## How It Works
1. **Execution:** Run `main.py` to start the image capture process.
2. **Image Acquisition:** The `image_acquisition.py` script interacts with the camera and continuously captures images.
3. **Queue Processing:** Captured images are added to a queue for analysis.
4. **Image Processing:** The `image_processor.py` script analyzes each image in the queue. If a snowflake is detected, the image is saved.
5. **Removal from Queue:** The image is removed from the queue after image processing.

## Requirements
Ensure you have the necessary dependencies installed before running the scripts. In a virtualenv, install the requirements as follws:
```bash
pip install -r requirements.txt
```
Additionally, the project requires PySpin, which needs to be installed from [source](https://catimapy.readthedocs.io/en/latest/camera_drivers_FLIRPySpin.html).

### Code Stucture
```
Snow-Drone
      ├── main.py                           <- main program logic
      ├── run_threads.py                    <- defines various operating modes
      ├── utils                             
      │      ├── hard_reset.py
      │      └── parser.py                  <- handles environment variables (flags)
      ├── weather_data                             
      │      └── read_trisonica.py          <- reads and logs anemometer data 
      └── imaging                             
             ├── image_acquisition.py       <- Captures images and stores them in a queue
             └── image_processing.py        <- Analyses images from queue and stores them if a snowflake is detected

```
All (sub-)processes are spawned from `main.py`.

## Usage
To start the image capture and processing, run:
```bash
python3 main.py
```
Program flags may be found under section [Parameters](#Parameters)

## Parameters
The following camera parameters can be changed by a command in the terminal at the start of the program.

1. **Exposure Time**
2. **Strobe Duration**
3. **Strobe Delay**
4. **Gain/ISO**
5. **Frame Rate**
6. **Queue Size**
7. **Test** (can be used in combination with **Number of Test Images**)
8. **Live** (displays a stream of captured images)
9. **Reset to default settings**
10. **Hard Reset**

An example is written below, which changes the exposure time to 150 microseconds:
```bash
python3 main.py --exposure_time 150
```

Help for usage may be found as follows:
```bash
python3 main.py --help
```

## Author
Léon Mamié - Master Student at IFD (ETH Zürich)

Vikram Damani - Master Student at ETH Zürich

