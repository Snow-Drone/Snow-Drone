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
        self.save_data = save_data
        self.kernel_x = np.array([[-1, 0, 1],
                                [-2, 0, 2],
                                [-1, 0, 1]])
        self.kernel_y = np.array([[1, 2, 1],
                                [0, 0, 0],
                                [-1, -2, -1]])
        
        # Create Sobel filter objects for GPU processing
        self.sobelx = cv2.createSobelFilter(0, -1, 1, 0, ksize=3)
        self.sobely = cv2.createSobelFilter(0, -1, 0, 1, ksize=3)

    def calculate_edges(self, image):
        """Calculates the amount of sharp edges in the image (GPU mat)."""
        # Calculate gradients of filtered image in x and y direction
        start = time.time_ns()
        # grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        # grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        # grad_x = cv2.filter2D(image.astype(np.float32), -1, self.kernel_x)
        # grad_y = cv2.filter2D(image.astype(np.float32), -1, self.kernel_y)
        grad_x = self.sobelx.apply(image)
        grad_y = self.sobely.apply(image)
        end = time.time_ns()
        elapsed = end - start
        print(f"[TIME] Sobel took {elapsed/1e6:.4f} ms")
        # # Calculate magnitudes and normalize them
        start = time.time_ns()
        magnitude = cv2.cuda.magnitude(grad_x, grad_y)
        end = time.time_ns()
        elapsed = end - start
        print(f"[TIME] Magnitude took {elapsed/1e6:.4f} ms")
        # laplacian = cv2.Laplacian(image,cv2.CV_64F)
        # magnitude = cv2.convertScaleAbs(laplacian)
        return magnitude

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
                # smoothed_image = cv2.GaussianBlur(image, (7, 7), sigmaX=2, sigmaY=2)
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(image)

                # Perform a Gaussian blur on the image using the GPU
                gpu_blurred_image = cv2.cuda.createGaussianFilter(gpu_image.type(), -1, (7, 7), 2)
                smoothed_image = gpu_blurred_image.apply(gpu_image)


                start = time.time_ns()
                magnitude = self.calculate_edges(smoothed_image)
                sharp_edges = self.calculate_sharp_edges(magnitude)
                # std = cp.std(magnitude)
                self.out_queue.put(sharp_edges)
                end = time.time_ns() 
                elapsed = end - start
                print(f"[TIME] Basic processing took {elapsed/1e6:.4f} ms")
                self.in_queue.task_done()
