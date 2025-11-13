"""This program runs preprocessing tasks and filters images that potentially contain snowflakes."""

import cv2
import os
import numpy as np
import torch
# import cupy as cp
import time 
from imaging.helper import gamma
from imaging.buffers import H, W, NBUF, buffers, free_q, ready_q
from utils.console_colours import info, warn, header, timef, queuef, err, bcolors

torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = False  # keep fast algos

torch.set_grad_enabled(False)
evt_start = torch.cuda.Event(enable_timing=True)
evt_end   = torch.cuda.Event(enable_timing=True)

# Global constants
DTYPE = torch.float16
conv_out = torch.ops.aten.convolution.out
# H, W = (1200, 1920) 


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
        self.padding = kernel_size // 2
        x = torch.arange(kernel_size, dtype=DTYPE).to(self.device) - self.padding
        gauss = torch.exp(-x**2 / (2 * sigma**2))
        gauss = gauss / gauss.sum()
        gauss_kernel = gauss[:, None] * gauss[None, :]
        self.gauss_kernel = gauss_kernel.view(1, 1, kernel_size, kernel_size).contiguous().mul_(1.0 / 255.0) # multiply by 1/255 to normlise image automatically
        
        
        # Sobel 3x3 x and y
        sobel_x = torch.tensor([[-1., 0., 1.],
                                [-2., 0., 2.],
                                [-1., 0., 1.]], dtype=DTYPE, device=self.device)
        sobel_y = torch.tensor([[-1., -2., -1.],
                                [0., 0., 0.],
                                [1., 2., 1.]], dtype=DTYPE, device=self.device)
        self.sobel_x = sobel_x.view(1, 1, 3, 3)
        self.sobel_y = sobel_y.view(1, 1, 3, 3)
        
        self.pinned = torch.empty((H, W), dtype=torch.uint8, pin_memory=True)
        self.dev_u8 = torch.empty((H, W), dtype=torch.uint8, device=self.device)
        self.x_fp   = torch.empty((1, 1, H, W), dtype=DTYPE, device=self.device)
        
        self.buf_blur = torch.empty_like(self.x_fp)
        self.buf_gx   = torch.empty_like(self.x_fp)
        self.buf_gy   = torch.empty_like(self.x_fp)
        self.buf_mag  = torch.empty_like(self.x_fp)
        self.buf_mask = torch.empty_like(self.x_fp, dtype=torch.bool)

        
        self.copy_stream = torch.cuda.Stream(priority=-1) 
        self.compute_stream = torch.cuda.Stream(priority=-1)
        
        self.gauss_conv = torch.nn.Conv2d(1,1,7, padding=3, bias=False).to('cuda', self.x_fp.dtype)
        self.gauss_conv.weight.data.copy_(gauss_kernel)  # [1,1,7,7]
        self.gauss_conv.weight.requires_grad_(False)

        self.sobelx = torch.nn.Conv2d(1,1,3, padding=1, bias=False).to('cuda', self.x_fp.dtype)
        self.sobely = torch.nn.Conv2d(1,1,3, padding=1, bias=False).to('cuda', self.x_fp.dtype)
        self.sobelx.weight.data.copy_(sobel_x); self.sobely.weight.data.copy_(sobel_y)
        for m in (self.gauss_conv, self.sobelx, self.sobely): m.eval()
        
        # self.compiled_sharp_edges = torch.compile(self.calculate_sharp_edges)
        
        ## sanity checks
        assert self.x_fp.is_cuda and self.dev_u8.is_cuda
        for k in (self.gauss_kernel, self.sobel_x, self.sobel_y):
            assert k.is_cuda and k.dtype == self.x_fp.dtype
    
    # @torch.no_grad()
    # def calculate_sharp_edges(self, tensor):
    #     thr = torch.tensor(100, dtype=self.x_fp.dtype, device=tensor.device)

    #     # Convs (allocation-free aside from the conv output copy_)
    #     with torch.backends.cudnn.flags(enabled=False):
    #         self.buf_blur.copy_(torch.nn.functional.conv2d(tensor, self.gauss_kernel, padding=self.padding, groups=1))
    #         self.buf_gx.copy_(torch.nn.functional.conv2d(self.buf_blur, self.sobel_x,     padding=1, groups=1))
    #         self.buf_gy.copy_(torch.nn.functional.conv2d(self.buf_blur, self.sobel_y,     padding=1, groups=1))

    #     # mag^2 (in-place, no new tensors)
    #     self.buf_mag.copy_(self.buf_gx)           # buf_mag = gx
    #     self.buf_mag.mul_(self.buf_gx)            # buf_mag = gx*gx
    #     self.buf_mag.add_(self.buf_gy.mul(self.buf_gy))  # buf_mag += gy*gy  (gy*gy reuses gy tensor)

    #     # mask & reduction WITHOUT compacting
    #     torch.gt(self.buf_mag, thr, out=self.buf_mask)   # bool mask in prealloc buffer
    #     self.buf_mag.mul_(self.buf_mask.to(self.buf_mag.dtype))  
    #     return self.buf_mag.sum()                        # 0-d CUDA tensor (no .item() here)
    
    @torch.no_grad()
    def calculate_sharp_edges(self, x):
        stride   = (1, 1)
        padding7 = (self.padding, self.padding)   # e.g., (3,3) for 7x7
        padding3 = (1, 1)
        dilation = (1, 1)
        transposed = False
        out_pad  = (0, 0)
        groups   = 1

        conv_out(
            x, self.gauss_kernel, None,
            stride, padding7, dilation,
            transposed, out_pad, groups,
            out=self.buf_blur
        )

        conv_out(
            self.buf_blur, self.sobel_x, None,
            stride, padding3, dilation,
            transposed, out_pad, groups,
            out=self.buf_gx
        )
        conv_out(
            self.buf_blur, self.sobel_y, None,
            stride, padding3, dilation,
            transposed, out_pad, groups,
            out=self.buf_gy
        )

        self.buf_mag.copy_(self.buf_gx)          # buf_mag = gx
        self.buf_mag.mul_(self.buf_gx)           # buf_mag = gx*gx
        self.buf_mag.addcmul_(self.buf_gy, self.buf_gy, value=1.0)  # + gy*gy

        thr_sq = 100
        self.buf_mag.add_(-thr_sq).relu_() # clips all values below the threshold to 0
        return self.buf_mag.sum()   # CUDA scalar

    
    # @torch.compile
    def process_images(self):
        """Continuously processes images from the queue until the process is stopped."""

        # Initialization of image counter and data container
        snowflake_number = 1
        with torch.no_grad():
            while not self.save_data.is_set():
                #Skip if queue empty
                if self.in_queue.empty():
                    continue

                try:
                    image = self.in_queue.get(timeout=0.1)   # block a bit; avoid busy-loop
                    t_wall0 = time.perf_counter()

                    if image.dtype is not np.uint8:
                        image = image.astype(np.uint8, copy=False)
                    assert image.flags['C_CONTIGUOUS'], "Non contiguous input"
                    
                    # Cast to toch tensor
                    t_h0 = time.perf_counter()
                    np.copyto(self.pinned.numpy(), image, casting='no')
                    t_h1 = time.perf_counter()
                    
                    # To CUDA
                    evt_start.record()
                    with torch.cuda.stream(self.copy_stream):
                        self.dev_u8.copy_(self.pinned, non_blocking=True)
                        
                    with torch.cuda.stream(self.compute_stream):
                        assert torch.cuda.current_stream().cuda_stream != torch.cuda.default_stream().cuda_stream
                        self.compute_stream.wait_stream(self.copy_stream)
                        self.x_fp.copy_(self.dev_u8.view(1,1,H,W), non_blocking=True)
                        sharp_edges = self.calculate_sharp_edges(self.x_fp)

                    # self.x_fp.copy_(self.dev_u8.view(1,1,H,W), non_blocking=True)   # [1,1,H,W] float16/32
                    # gpu_u8 = self.pinned.to("cuda", non_blocking=True)
                    # # image_tensor = gpu_u8.permute(2,0,1).to(torch.float32).mul_(1/255) # Normalise and permute to expected order by torch
                    # image_tensor = gpu_u8.unsqueeze(0).unsqueeze(0).to(DTYPE).mul_(1/255.0)
                    # image_tensor = image_tensor.to(memory_format=torch.channels_last)
                    
                    # sharp_edges = self.calculate_sharp_edges(self.x_fp)
                    evt_end.record()
                    evt_end.synchronize()  # finalize GPU timing window
                    

                    if sharp_edges.item() > self.thresh:
                        # Don't write to full queue
                        if self.out_queue.full():
                            print("Snowflake queue full")
                            continue
                        
                        self.out_queue.put_nowait(image)
                        print(f"[INFO] Snowflake {snowflake_number} detected and added to processing queue.")
                        snowflake_number += 1
                        
                    t_wall1 = time.perf_counter()
                    
                    gpu_ms   = evt_start.elapsed_time(evt_end)
                    host_ms  = (t_h1 - t_h0) * 1e3
                    total_ms = (t_wall1 - t_wall0) * 1e3
                    print(f"[Processing] total={total_ms:.3f} ms  gpu={gpu_ms:.3f} ms  host_copy={host_ms:.3f} ms")
                        
                finally:
                    self.in_queue.task_done()
                    
                # end = time.time_ns()
                # duration = end - start
                # print(f"[Processing] took {duration/1e6} ms")