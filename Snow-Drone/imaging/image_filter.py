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
            if self.in_queue.empty():
                continue
            image = self.in_queue.get(False)
            self.in_queue.task_done()
            
            image = image.download()
            # Calculate sharp edges
            sharp_edges = self.calculate_sharp_edges(image)
            if sharp_edges > self.threshold:
                if self.out_queue.full():
                    print("Snowflake queue full.")
                    continue
                
                self.out_queue.put(image)
                info(f"Image passed the filter with {sharp_edges} sharp edges.")

                    
            
        info(f"Finished all filtering")
