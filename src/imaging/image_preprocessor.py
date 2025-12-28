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
        self.kernel_x = np.array([[-1, 0, 1],
                                  [-2, 0, 2],
                                  [-1, 0, 1]])
        self.kernel_y = np.array([[1, 2, 1],
                                  [0, 0, 0],
                                  [-1, -2, -1]])
               
    def flip_image(self, image):
        """Flips an image from the queue that it has the correct orientation."""
        return np.flipud(np.fliplr(image))

    def calculate_edges(self, image):
        """Calculates the amount of sharp edges in the image."""
        grad_x = cv2.filter2D(image.astype(np.float32), -1, self.kernel_x)
        grad_y = cv2.filter2D(image.astype(np.float32), -1, self.kernel_y)


        # # Calculate magnitudes
        magnitude = cv2.magnitude(grad_x, grad_y)

        # laplacian = cv2.Laplacian(image,cv2.CV_64F)
        # magnitude = cv2.convertScaleAbs(laplacian)
        return magnitude
    
    def calculate_sharp_edges(self, image):
        threshold = 10 # Empirical threshold for sharp edges
        sharp_edges = np.sum(image > threshold)
        return sharp_edges

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""

        # Initialization of image counter and data container
        snowflake_number = 1

        while not self.save_data.is_set():
            #Skip if queue empty
            if self.in_queue.empty():
                continue

            # Get image from queue and flip it 180 degrees
            start = time.time_ns()
            image, date = self.in_queue.get(False) # Non-blocking
            self.in_queue.task_done()
            # image = np.frombuffer(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())

            # Remove the high frequency noise with the gaussian blur filter
            smoothed_image = cv2.GaussianBlur(image, (7, 7), sigmaX=2, sigmaY=2) # FIXME: 5x5 is faster, but not yet tested

            # Save image if the amount of sharp edges in it are above a defined threshold
            magnitude = self.calculate_edges(smoothed_image)
            sharp_edges = self.calculate_sharp_edges(magnitude)
            
            intensity_counts_above_10 = np.sum(smoothed_image > 30)
            # print(f"[DEBUG] Sharp edges: {sharp_edges}, Intensity counts above 30: {intensity_counts_above_10}")

            if (sharp_edges > self.thresh) or (intensity_counts_above_10 > self.thresh * 4):
                # Don't write to full queue
                if self.out_queue.full():
                    print("Snowflake queue full")
                    continue
                
                self.out_queue.put_nowait((image, date)) # put the unsmoothed image into queue
                print(f"[INFO] Snowflake {snowflake_number} detected and added to processing queue.")
                snowflake_number += 1

            # end = time.time_ns()
            # duration = end - start
            # print(f"PROCESSING took {duration/1e6} ms")