"""This program runs postprocessing tasks to save useful images and empties the queue."""

import cv2
import os
import numpy as np
import time
from scipy.signal import savgol_coeffs

class ImageProcessor:
    def __init__(self, config, queue):
        self.queue = queue
        self.config = config

        # Define the location of the folder to save the images 
        parent_dir="/home/orin/Snowscope/pictures_Leon"

        # Make directory with name {M-D_H:M:S}
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
        """Flips an image from the queue that it has the correct orientation"""

        # Convert PySpin image to NumPy array
        image_array = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())

        # Flip the image vertically and horizontally (180 degrees rotation)
        return np.flipud(np.fliplr(image_array))

    def calculate_sharp_edges(self, image):
        """Calculates the amount of sharp edges in the image"""

        # Calculate gradients of filtered image in x and y direction
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate magnitudes and normalize them
        grad_magnitude = cv2.magnitude(grad_x, grad_y)
        grad_magnitude_norm = cv2.normalize(grad_magnitude, None, 0, 255, cv2.NORM_MINMAX)

        # Count amount of sharp edges
        threshold = 75 # Empirical threshold for sharp edges
        sharp_edges = np.sum(grad_magnitude_norm > threshold)
        print(sharp_edges)

        return sharp_edges

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""

        # Initialization of image counter
        snowflake_number = 1

        while True:
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

                else:
                    print("No snowflake detected or not in focus.")
                
                # Remove processed image from queue
                self.queue.task_done()
