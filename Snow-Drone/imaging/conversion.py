import PySpin
import os
import typing
import cv2
import numpy as np
from utils.console_colours import info, warn, header, timef, queuef, err

class ImageConverter:
    
    def __init__(self, in_queue, out_queue, stream, finished):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.stream = stream
        self.finished = finished
        
    
    def convert(self):
        while not self.finished.is_set():
            if self.in_queue.empty():
                continue
            
            image = self.in_queue.get()
            image = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())
            src = cv2.cuda_GpuMat()
            src.upload(image, self.stream)
            self.out_queue.put(src)
            queuef(f"size: {self.out_queue.qsize()}", 2)
            self.in_queue.task_done()
        info(f"Finished all conversions")
