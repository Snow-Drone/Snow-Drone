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
        snowflake_number = 0
        while not self.save_data.is_set():
            if not self.in_queue.empty():
                image = self.in_queue.get()
                self.in_queue.task_done()
                snowflake_number += 1
                # Process the image to detect snowflakes
                                    # Create file in previously generated folder
                filename = os.path.join(self.path, f"Snowflake_{snowflake_number}.bmp")
                # Save image in file
                cv2.imwrite(filename, image)
                print(f"Saved potential snowflake: {filename}")

                # Create binary image with defined threshold
                thresh = 12
                binary_image = ((image > thresh) * 255)
                # Morphological closing to fill small holes inside snowlakes
                kernel = np.ones((15, 15), np.uint8)
                closed_binary_image = cv2.morphologyEx(binary_image.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=3)
                # Calculate regions of snowflakes in image
                label_img = label(closed_binary_image)
                snowflakes = regionprops(label_img)
                # Initialize a list to store characteristic values of snowflakes
                list = []

                for snowflake in snowflakes:
                    # Only save the snowflakes that are bigger than 50 pixel in diameter
                    if snowflake.equivalent_diameter_area >= 50:
                        # Append center of snowflake
                        list.append(snowflake.centroid)
                        # Append orientation of snowflake in grad
                        list.append((180*snowflake.orientation)/math.pi)
                        # Append aspect ratio of snowflake
                        list.append(snowflake.axis_minor_length/snowflake.axis_major_length)
                        # Append diameter in micrometers
                        list.append(snowflake.equivalent_diameter_area*pixel_size)
                        # Append complexity parameter of snowflake
                        list.append(snowflake.perimeter/(math.pi*snowflake.equivalent_diameter_area))
                
                # Store the data list together with their filename
                data[filename] = list

                # Remove processed image from queue

        # Create a csv file to save the data
        output_filename = "image_data.csv"
        output_path = os.path.join(self.path, output_filename)
        # Write the data into the created csv file
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            # Define header
            writer.writerow(["image path", "values (center of centroid, orientation, aspect ratio, diameter, complexity)"])
            # Write values of all saved images to the csv file
            print(f"Captured {len(data)} snowflakes")
            for image_name, values in data.items():
                writer.writerow([image_name, json.dumps(values)])
                # Save the processed image and data
                # (Implementation of saving goes here)