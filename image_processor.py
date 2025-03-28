"""This program will run postprocessing tasks to save valuable images and empty the queue."""

import cv2
import os
import numpy as np
import time

class ImageProcessor:
    def __init__(self, config, queue):
        self.queue = queue
        self.config = config

        # Define the location of the folder to save the images 
        parent_dir="/home/orin/Snowscope/pictures_Leon"

        # Make directory with name {M-D_H:M:S}
        current_time_tuple=time.localtime()
        directory = f"{current_time_tuple[1]}-{current_time_tuple[2]}_{current_time_tuple[3]}:{current_time_tuple[4]}:{current_time_tuple[5]}"

        self.path=os.path.join(parent_dir,directory)

        try:
            os.mkdir(self.path)
            print("Directory '%s' created" %self.path)

        except OSError as error:
            print("Error:", error)
            return False
        
    def flip_image(self, image):
        """Flip image from queue that it has the correct orientation"""

        # Convert PySpin image to NumPy array
        image_array = np.array(image.GetData(), dtype=np.uint8).reshape(image.GetHeight(), image.GetWidth())

        # Flip the image vertically and horizontally (180 degrees rotation)
        return np.flipud(np.fliplr(image_array))

    def measure_blurriness(self, image):
        """Calculate the overall blurriness of the picture"""

        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        variance = laplacian.var()
        return variance

    def process_images(self):
        """Continuously process images from the queue until the process is stopped."""
        snowflake_number = 1

        while True:
            if not self.queue.empty():
                # Get image from queue and flip it 180 degrees
                image = self.queue.get()
                image_flipped = self.flip_image(image)
                # Calculate the blurriness variance
                blurriness = self.measure_blurriness(image_flipped)

                # Save image if it fullfills certain requirements
                if blurriness < 50:
                    filename = os.path.join(self.path, f"Snowflake_{snowflake_number}.bmp")
                    snowflake_number += 1
                    cv2.imwrite(filename, image_flipped)
                    print(f"Saved potential snowflake: {filename}")
                else:
                    print("No snowflake detected or not in focus.")
                
                # Remove processed image from queue
                self.queue.task_done()
