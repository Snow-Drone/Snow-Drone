"""This program runs postprocessing tasks to save useful images and empties the queue."""

import cv2
import os
import numpy as np
# import cupy as cp
import time 
from imaging.helper import gamma
from utils.console_colours import info, warn, header, timef, queuef, err, bcolors



class ImagePreProcessor:
    def __init__(self, config, in_queue, out_queue, finished):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.finished = finished
        # prepare GPU filters
        self.gpu_blurred_image = cv2.cuda.createGaussianFilter(0, -1, (7, 7), 2)
        self.sobelx = cv2.cuda.createSobelFilter(0, -1, 1, 0, ksize=3)
        self.sobely = cv2.cuda.createSobelFilter(0, -1, 0, 1, ksize=3)

    def calculate_edges(self, image):
        """Calculates the amount of sharp edges in the image (GPU mat)."""
        grad_x = self.sobelx.apply(image)
        grad_y = self.sobely.apply(image)
        
        magnitude = cv2.cuda.addWeighted(grad_x, 0.5, grad_y, 0.5,0)
        return magnitude

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""
        while not self.finished.is_set():
            if not self.in_queue.empty():
                # Get image from queue and flip it 180 degrees
                image = self.in_queue.get()
                
                # Perform a Gaussian blur on the image using the GPU
                smoothed_image = self.gpu_blurred_image.apply(image)


                start = time.time_ns()
                magnitude = self.calculate_edges(smoothed_image)
                # std = cp.std(magnitude)
                self.out_queue.put(magnitude)
                end = time.time_ns() 
                elapsed = end - start
                timef(f"Basic processing took {elapsed/1e6:.4f} ms")
                # queuef(f"size: {self.out_queue.qsize()}", 3)
                self.in_queue.task_done()
                
        info(f"Finished all preprocessing")
