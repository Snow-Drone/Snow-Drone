import os
import cv2
import numpy as np
import time
from utils.console_colours import info, warn, header, timef, queuef, err

class ImageFilter:
    def __init__(self, config, in_queue, out_queue, finished):
        self.threshold = config["sharp_edges_threshold"]
        self.cutoff = config["cutoff_threshold"]
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.finished = finished
        
        # preallocate gpu mat 
        
    def calculate_sharp_edges(self, image):
        # Count amount of sharp edges
        sharp_edges = np.sum(image > self.cutoff)
        return sharp_edges

    def filter_images(self):
        """Filters the image based on the defined threshold."""
        while not self.finished.is_set():
            while not self.in_queue.empty():
                image = self.in_queue.get()
                start = time.time_ns()
                # download to cpu
                image = image.download()
                # Calculate sharp edges
                sharp_edges = self.calculate_sharp_edges(image)
                if sharp_edges > self.threshold:
                    self.out_queue.put(image)
                    info(f"Image passed the filter with {sharp_edges} sharp edges.")
                    
                self.in_queue.task_done()
                end = time.time_ns()
                elapsed = end - start
                # timef(f"Sharp edges took {elapsed/1e6:.4f} ms")
                # queuef(f"size: {self.out_queue.qsize()}", 4)
        
        info(f"Finished all filtering")
