import os
import threading
import time


class ImageScanner:

    IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')

    def __init__(self, monitored_folder, ring_buffer, scan_interval=5):
        self.monitored_folder = monitored_folder
        self.ring_buffer = ring_buffer
        # observed_files stores filenames we've already seen
        self.observed_files = set()
        self.scan_interval = scan_interval
        self._stop_event = threading.Event()
        self._thread = None

    def scan_once(self):
        try:
            it = os.scandir(self.monitored_folder)
        except FileNotFoundError:
            return

        new_found = []
        for entry in it:
            # only consider regular files with the right extension
            try:
                if not entry.is_file():
                    continue
            except Exception:
                # on some filesystems is_file may fail; skip defensively
                continue
            name = entry.name
            if name in self.observed_files:
                continue
            lname = name.lower()
            if lname.endswith(self.IMAGE_EXTS):
                new_found.append(name)

        # sort to provide deterministic ordering for tests / UI
        for name in sorted(new_found):
            full = os.path.join(self.monitored_folder, name)
            self.ring_buffer.add(full)

        # update observed set after processing so we don't miss files
        self.observed_files.update(new_found)

    def _scan_loop(self):
        while not self._stop_event.is_set():
            self.scan_once()
            time.sleep(self.scan_interval)

    def start_scanning(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop_scanning(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)