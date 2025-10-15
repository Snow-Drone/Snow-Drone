import serial
from datetime import datetime
import time

class DataLogger:
    def __init__(self, save_data, port='/dev/ttyUSB0', baud_rate=115200, log_file_name='trisonica.log'):
        self.save_data = save_data
        # Define port and baud rate to receive sensor data
        self.port = port
        self.baud_rate = baud_rate

        # Open serial port
        self.ser = serial.Serial(port, baud_rate, timeout=1)

        # Initialize log file
        current_time = time.strftime("%Y-%m-%d_%a_%H:%M:%S")
        os.makedirs("output", exist_ok=True)
        
        log_dir = os.path.join("output/", f"{current_time}")
        os.makedirs(log_dir, exist_ok=True)
        
        self.log_file_path = os.path.join(log_dir, log_file_name)
        
    def log_data(self):
        print("Logging started. Press Ctrl+C to stop.")
        ser = self.ser

        try:
            with open(self.log_file_path, 'a') as log_file:
                while not self.save_data.is_set():
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        timestamped_line = f"{datetime.now().isoformat()} - {line}"
                        print(timestamped_line)
                        log_file.write(timestamped_line + '\n')
                        log_file.flush()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            ser.close()