"""This program runs postprocessing tasks to save useful images and empties the queue."""

import cv2
import os
import numpy as np
# import cupy as cp
import time 
from imaging.helper import gamma


class ImagePreProcessor:
    def __init__(self, config, in_queue, out_queue, save_data):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.thresh = config["sharp_edges_threshold"]
        self.save_data = save_data
        
    def flip_image(self, image):
        """Flips an image from the queue that it has the correct orientation."""
        return np.flipud(np.fliplr(image))

    def calculate_edges(self, image):
        """Calculates the amount of sharp edges in the image."""

        # Calculate gradients of filtered image in x and y direction
        start = time.time_ns()
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        end = time.time_ns()
        elapsed = end - start
        print(f"[TIME] Sobel took {elapsed/1e6:.4f} ms")

        # # Calculate magnitudes and normalize them
        start = time.time_ns()
        magnitude = cv2.magnitude(grad_x, grad_y)
        end = time.time_ns()
        elapsed = end - start
        print(f"[TIME] Magnitude took {elapsed/1e6:.4f} ms")
        # laplacian = cv2.Laplacian(image,cv2.CV_64F)
        # magnitude = cv2.convertScaleAbs(laplacian)
        return magnitude
    
    def calculate_sharp_edges(self, image):
        # Count amount of sharp edges
        threshold = 10 # Empirical threshold for sharp edges
        start = time.time_ns()
        sharp_edges = np.sum(image > threshold)
        end = time.time_ns()
        elapsed = end - start
        print(f"[TIME] Sharp edges took {elapsed/1e6:.4f} ms")
        # print("Number of sharp edges:", sharp_edges)
        return sharp_edges

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""

        # Initialization of image counter and data container
        snowflake_number = 1

        while not self.save_data.is_set():
            if not self.in_queue.empty():
                # Get image from queue and flip it 180 degrees
                image = self.in_queue.get()
                image = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())

                # image = self.flip_image(image)

                # Remove the high frequency noise with the gaussian blur filter
                smoothed_image = cv2.GaussianBlur(image, (7, 7), sigmaX=2, sigmaY=2)

                # Save image if the amount of sharp edges in it are above a defined threshold
                start = time.time_ns()
                magnitude = self.calculate_edges(smoothed_image)
                sharp_edges = self.calculate_sharp_edges(magnitude)
                # std = cp.std(magnitude)
                if  sharp_edges > self.thresh:
                    # Put the processed image into the output queue for further processing
                    self.out_queue.put(smoothed_image)
                    print(f"[INFO] Snowflake {snowflake_number} detected and added to processing queue.")
                    snowflake_number += 1
                end = time.time_ns() 
                elapsed = end - start
                print(f"[TIME] Basic processing took {elapsed/1e6:.4f} ms")
                self.in_queue.task_done()
