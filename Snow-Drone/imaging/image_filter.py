import os
import cv2
import numpy as np
import time

class ImageFilter:
    def __init__(config, self, in_queue, out_queue):
        self.threshold = config["sharp_edges_threshold"]
        self.cutoff = config["cutoff_threshold"]
        self.in_queue = in_queue
        self.out_queue = out_queue
        
    def calculate_sharp_edges(self, image):
        # Count amount of sharp edges
        start = time.time_ns()
        sharp_edges = np.sum(image > self.cutoff)
        end = time.time_ns()
        elapsed = end - start
        print(f"[TIME] Sharp edges took {elapsed/1e6:.4f} ms")
        # print("Number of sharp edges:", sharp_edges)
        return sharp_edges

    def filter_images(self):
        """Filters the image based on the defined threshold."""
        while not self.in_queue.empty():
            image = self.in_queue.get()
            # download to cpu
            image = image.download()
            # Calculate sharp edges
            sharp_edges = self.calculate_sharp_edges(image)
            if sharp_edges > self.threshold:
                self.out_queue.put(image)
                print(f"[INFO] Image passed the filter with {sharp_edges} sharp edges.")