import PySpin
import os
import typing
import cv2
import numpy as np

class ImageConverter:
    
    def __init__(self, in_queue, out_queue, finished):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.finished = finished
    
    def convert(self):
        while not self.finished.is_set():
            while not self.in_queue.empty():
                image = self.in_queue.get()
                image = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(image)
                self.out_queue.put(gpu_image)
                self.in_queue.task_done()
        print(f"[INFO] Finished all conversions")
