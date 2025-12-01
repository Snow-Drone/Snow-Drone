import cv2
import os
import numpy as np
import time
from scipy.signal import savgol_coeffs
from skimage.measure import label, regionprops
import math
import csv
import json

class SnowflakeProcessor:
    def __init__(self, config, in_queue, save_data):
        self.in_queue = in_queue
        self.config = config
        self.save_data = save_data

        # Define the location of the folder to save the images 
        parent_dir="/mnt/nvme/pictures/snow_drone_images/"

        # Make directory with name {Months-Days_Hours:Minutes:Seconds}
        current_time_tuple=time.localtime()
        directory = f"{current_time_tuple[1]}-{current_time_tuple[2]}_{current_time_tuple[3]}-{current_time_tuple[4]}-{current_time_tuple[5]}"
        self.path=os.path.join(parent_dir,directory)

        try:
            os.makedirs(self.path, exist_ok=False) # fail if the directory already exists
            print("Directory '%s' created" %self.path)

        except OSError as error:
            print("Error:", error)
            return False
        
    def __del__(self):
        print(f"All images saved to {self.path} (in case you missed it first time...)")
        
    def process_snowflakes(self):
        """Processes a snowflake image from the queue."""
        pixel_size = 5.86 # in [um]
        data = {}
        factor = 2
        
        snowflake_number = 0
        while not self.save_data.is_set():
            if not self.in_queue.empty():
                image, date = self.in_queue.get()
                self.in_queue.task_done()
                snowflake_number += 1
                # Process the image to detect snowflakes
                                    # Create file in previously generated folder
                print(f"Processing snowflake number {snowflake_number} taken at {date}")
                filename = os.path.join(self.path, f"{date}_Snowflake_{snowflake_number}.bmp")
                # Save image in file
                cv2.imwrite(filename, image)
                print(f"Saved potential snowflake: {filename}")
                
                
                ################################################
                # downsampling template
                # smooth = cv2.bilateralFilter(image, d=5, sigmaColor=75, sigmaSpace=75) # optional, uncomment only if sure
                
                # resize image
                # h, w = image.shape[:2]
                # new_w = w // factor
                # new_h = h // factor
                
                # INTER_AREA uses pixel area relation - very close to proper averaging
                # image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                
                # unsharp masking maybe (also optional)
                # blur = cv2.GaussianBlur(image, (0, 0), sigmaX=1.0)
                # sharp = cv2.addWeighted(image, 1.7, blur, -0.7, 0)
