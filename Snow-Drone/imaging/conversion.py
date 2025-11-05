import PySpin
import os
import typing
import time
import cv2
import numpy as np
from utils.console_colours import info, warn, header, timef, queuef, err

class ImageConverter:
    
    def __init__(self, in_queue, out_queue, stream, finished):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.stream = stream
        self.finished = finished
        
        src = np.empty((1920, 1200), dtype=np.uint8)           
        self.src = cv2.cuda.registerPageLocked(src)       
                
    
    def convert(self):
        while not self.finished.is_set():
            if self.in_queue.empty():
                continue
            start = time.time_ns()
            image = self.in_queue.get()
            self.in_queue.task_done()
            self.src = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(self.src, self.stream)
            self.out_queue.put(gpu_image)
            end = time.time_ns()
            duration = end - start
            queuef(f"size: {self.out_queue.qsize()}, took {duration/1e6} ms", 2)

        info(f"Finished all conversions")
