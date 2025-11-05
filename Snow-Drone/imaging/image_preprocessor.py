"""This program runs postprocessing tasks to save useful images and empties the queue."""

import cv2
import os
import numpy as np
# import cupy as cp
import time 
from imaging.helper import gamma
from utils.console_colours import info, warn, header, timef, queuef, err, bcolors



class ImagePreProcessor:
    def __init__(self, config, in_queue, out_queue, stream, finished):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.finished = finished
        self.threshold = config["sharp_edges_threshold"]

        # prepare GPU filters
        self.stream = stream
        self.gauss = cv2.cuda.createGaussianFilter(srcType=cv2.CV_8UC1, dstType=cv2.CV_8UC1,
                                     ksize=(3,3), sigma1=0, sigma2=0, rowBorderMode=cv2.BORDER_DEFAULT, columnBorderMode=cv2.BORDER_DEFAULT) # (7,7), 2
        self.sobelx = cv2.cuda.createSobelFilter(cv2.CV_8UC1, cv2.CV_32F, 1, 0, 3)
        self.sobely = cv2.cuda.createSobelFilter(cv2.CV_8UC1, cv2.CV_32F, 0, 1, 3)
        
        w, h = (1200, 1920)
        # self.d_src    = cv2.cuda_GpuMat(h, w, cv2.CV_8UC1)
        self.d_blur   = cv2.cuda_GpuMat(h, w, cv2.CV_8UC1)
        self.d_gx     = cv2.cuda_GpuMat(h, w, cv2.CV_32FC1)
        self.d_gy     = cv2.cuda_GpuMat(h, w, cv2.CV_32FC1)
        self.d_mag    = cv2.cuda_GpuMat(h, w, cv2.CV_32FC1)
        self.d_mag8   = cv2.cuda_GpuMat(h, w, cv2.CV_8UC1)
        self.d_mag16  = cv2.cuda_GpuMat(h, w, cv2.CV_16SC1)
        self.d_bin    = cv2.cuda_GpuMat(h, w, cv2.CV_8UC1)
        # self.d_int    = cv2.cuda_GpuMat(h, w, cv2.CV_32S)

    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""
        while not self.finished.is_set():
            if self.in_queue.empty():
                continue
            # Get image from queue and flip it 180 degrees
            image = self.in_queue.get()
            # Upload (async)
            start = time.time_ns()
            # Gaussian → SobelX/Y → magnitude (all on same stream)
            self.gauss.apply(image, self.d_blur, self.stream)
            self.sobelx.apply(self.d_blur, self.d_gx, self.stream)
            self.sobely.apply(self.d_blur, self.d_gy, self.stream)
            cv2.cuda.magnitude(self.d_gx, self.d_gy, self.d_mag, self.stream)
            self.stream.waitForCompletion()
            
            end = time.time_ns()
            elapsed = end - start

            self.out_queue.put(image)                
            elapsed = end - start
            timef(f"Basic processing took {elapsed/1e6:.4f} ms")
            # queuef(f"size: {self.out_queue.qsize()}", 3)
            self.in_queue.task_done()
                
        info(f"Finished all preprocessing")
