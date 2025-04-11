"""This program runs postprocessing tasks to save useful images and empties the queue."""

import cv2
import os
import numpy as np
import time
from scipy.signal import savgol_coeffs
from skimage.measure import label, regionprops
import math
import csv
import json

class ImageProcessor:
    def __init__(self, config, queue, save_data):
        self.queue = queue
        self.config = config
        self.save_data = save_data

        # Define the location of the folder to save the images 
        parent_dir="/home/orin/Snowscope/pictures_Leon"

        # Make directory with name {Months-Days_Hours:Minutes:Seconds}
        current_time_tuple=time.localtime()
        directory = f"{current_time_tuple[1]}-{current_time_tuple[2]}_{current_time_tuple[3]}-{current_time_tuple[4]}-{current_time_tuple[5]}"
        self.path=os.path.join(parent_dir,directory)

        try:
            os.mkdir(self.path)
            print("Directory '%s' created" %self.path)

        except OSError as error:
            print("Error:", error)
            return False
        
    def flip_image(self, image):
        """Flips an image from the queue that it has the correct orientation."""

        # Convert PySpin image to NumPy array
        image_array = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())

        # Flip the image vertically and horizontally (180 degrees rotation)
        return np.flipud(np.fliplr(image_array))

    def calculate_sharp_edges(self, image):
        """Calculates the amount of sharp edges in the image."""

        # Calculate gradients of filtered image in x and y direction
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate magnitudes and normalize them
        grad_magnitude = cv2.magnitude(grad_x, grad_y)
        grad_magnitude_norm = cv2.normalize(grad_magnitude, None, 0, 255, cv2.NORM_MINMAX)

        # Count amount of sharp edges
        threshold = 75 # Empirical threshold for sharp edges
        sharp_edges = np.sum(grad_magnitude_norm > threshold)
        print("Number of sharp edges:", sharp_edges)

        return sharp_edges

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""

        # Initialization of image counter and data container
        snowflake_number = 1
        data = {}

        # Define the size of a pixel
        pixel_size = 5.86 # in [um]

        while not self.save_data.is_set():
            if not self.queue.empty():
                # Get image from queue and flip it 180 degrees
                image = self.queue.get()
                image_flipped = self.flip_image(image)

                # Define Savitzky-Golay filter parameters and get coefficients
                window_length = 11 # Filter size
                polyorder = 2 # Polynomial order
                coeffs = savgol_coeffs(window_length, polyorder).astype(np.float32)

                # Convert coefficients to row and column vectors
                row_coeffs = coeffs.reshape(1, -1)
                column_coeffs = coeffs.reshape(-1, 1)
                
                # Apply 1D filter along rows (horizontal smoothing)
                smoothed_rows = cv2.sepFilter2D(image_flipped.astype(np.float32), ddepth=-1, kernelX=row_coeffs, kernelY=np.array([[1]], dtype=np.float32))

                # Apply 1D filter along columns (vertical smoothing)
                smoothed_image = cv2.sepFilter2D(smoothed_rows, ddepth=-1, kernelX=np.array([[1]], dtype=np.float32), kernelY=column_coeffs)

                # Covert image back to uint8 format
                smoothed_image = np.clip(smoothed_image, 0, 255).astype(np.uint8)

                # Save image if the amount of sharp edges in it are above a defined threshold
                if self.calculate_sharp_edges(smoothed_image) > self.config["sharp_edges_threshold"]:
                    # Create file in previously generated folder
                    filename = os.path.join(self.path, f"Snowflake_{snowflake_number}.bmp")
                    # Save image in file
                    cv2.imwrite(filename, image_flipped)
                    snowflake_number += 1
                    print(f"Saved potential snowflake: {filename}")

                    # Create binary image with defined threshold
                    thresh = 12
                    binary_image = ((smoothed_image > thresh) * 255)
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

                else:
                    print("No snowflake detected or not in focus.")
                
                # Remove processed image from queue
                self.queue.task_done()

        # Create a csv file to save the data
        output_filename = "image_data.csv"
        output_path = os.path.join(self.path, output_filename)
        # Write the data into the created csv file
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            # Define header
            writer.writerow(["image path", "values (center of centroid, orientation, aspect ratio, diameter, complexity)"])
            # Write values of all saved images to the csv file
            for image_name, values in data.items():
                writer.writerow([image_name, json.dumps(values)])
