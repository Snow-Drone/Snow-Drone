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

class ImagePreProcessor:
    def __init__(self, config, in_queue, out_queue, save_data):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.config = config
        self.save_data = save_data
        
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

        # Count amount of sharp edges
        threshold = 10 # Empirical threshold for sharp edges
        sharp_edges = np.sum(grad_magnitude > threshold)
        print("Number of sharp edges:", sharp_edges)

        return sharp_edges

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""

        # Initialization of image counter and data container
        snowflake_number = 1

        while not self.save_data.is_set():
            if not self.in_queue.empty():
                # Get image from queue and flip it 180 degrees
                image = self.in_queue.get()
                image_flipped = self.flip_image(image)

                # Remove the high frequency noise with the gaussian blur filter
                smoothed_image = cv2.GaussianBlur(image_flipped, (25, 25), sigmaX=2, sigmaY=2)

                # Save image if the amount of sharp edges in it are above a defined threshold
                if self.calculate_sharp_edges(smoothed_image) > self.config["sharp_edges_threshold"]:
                    # Put the processed image into the output queue for further processing
                    self.out_queue.put(smoothed_image)
                    print(f"[INFO] Snowflake {snowflake_number} detected and added to processing queue.")
                    snowflake_number += 1
