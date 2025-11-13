import numpy as np
import queue

H, W, NBUF = 1200, 1920, 10
buffers = [np.empty((H, W), np.uint8) for _ in range(NBUF)]
free_q  = queue.Queue(maxsize=NBUF)
ready_q = queue.Queue(maxsize=NBUF)
