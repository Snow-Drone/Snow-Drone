"""This program runs preprocessing tasks and filters images that potentially contain snowflakes."""

import cv2
import os
import numpy as np
import torch
# import cupy as cp
import time 
from imaging.helper import gamma
from utils.console_colours import info, warn, header, timef, queuef, err, bcolors


class ImagePreProcessor:
    def __init__(self, config, in_queue, out_queue, save_data):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.thresh = config["sharp_edges_threshold"]
        self.save_data = save_data
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Using device:", self.device)
        _ = torch.empty((1,), device=self.device) # warm up gpu
        
        # Convolve with gaussian kernel on torch device
        kernel_size = 7
        sigma = 2.0
        x = torch.arange(-kernel_size // 2 + 1., kernel_size // 2 + 1.).to(self.device)
        gauss = torch.exp(-x**2 / (2 * sigma**2))
        gauss = gauss / gauss.sum()
        gauss_kernel = gauss[:, None] @ gauss[None, :]
        self.gauss_kernel = gauss_kernel.expand(3, 1, kernel_size, kernel_size)
        
        self.padding = kernel_size // 2
        
        # Sobel 3x3 x and y
        sobel_x = torch.tensor([[-1., 0., 1.],
                                [-2., 0., 2.],
                                [-1., 0., 1.]], device=self.device)
        sobel_y = torch.tensor([[-1., -2., -1.],
                                [0., 0., 0.],
                                [1., 2., 1.]], device=self.device)
        self.sobel_x = sobel_x.expand(3, 1, 3, 3)
        self.sobel_y = sobel_y.expand(3, 1, 3, 3)
        
        H, W, C = (1200, 1920, 1) # FIXME: Verify that images are in mono     
        self.pinned = torch.empty((H, W, C), dtype=torch.uint8, pin_memory=True)

    
    def calculate_sharp_edges(self, tensor):
        threshold = 10 # Empirical threshold for sharp edges
        
        torch.cuda.synchronize()
        blurred_image_tensor = torch.nn.functional.conv2d(tensor, self.gauss_kernel, padding=self.padding, groups=3)
        grad_x = torch.nn.functional.conv2d(blurred_image_tensor, self.sobel_x, padding=1, groups=3)
        grad_y = torch.nn.functional.conv2d(blurred_image_tensor, self.sobel_y, padding=1, groups=3)
        gradient_magnitude = torch.sqrt(grad_x ** 2 + grad_y ** 2)
        s = gradient_magnitude[gradient_magnitude > threshold].sum() 
        torch.cuda.synchronize()
        
        sharp_edges = s.item()
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
            image = self.in_queue.get(False) # Non-blocking
            self.in_queue.task_done()
            
            # Cast to Np array
            image = np.frombuffer(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())
            
            # Cast to toch tensor
            torch.cuda.synchronize()
            np.copyto(self.pinned.numpy(), image) 
            
            # To CUDA
            gpu_u8 = self.pinned.to("cuda", non_blocking=True)
            image_tensor = gpu_u8.permute(2,0,1).to(torch.float32).mul_(1/255) # Normalise and permute to expected order by torch
            
            sharp_edges = self.calculate_sharp_edges(image_tensor)
            

            if sharp_edges > self.thresh:
                # Don't write to full queue
                if self.out_queue.full():
                    print("Snowflake queue full")
                    continue
                
                self.out_queue.put_nowait(image)
                print(f"[INFO] Snowflake {snowflake_number} detected and added to processing queue.")
                snowflake_number += 1

            end = time.time_ns()
            duration = end - start
            print(f"[Processing] took {duration/1e6} ms")