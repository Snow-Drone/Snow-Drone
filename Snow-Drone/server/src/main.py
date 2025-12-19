from server.src.server import WebServer
from server.src.scanner import ImageScanner
import argparse
from typing import Optional


def serve(host: str = '0.0.0.0', port: int = 5000, debug: bool = False, ring_size: Optional[int] = None, path: str = ""):
    if ring_size is None:
        ring_size = 10
    ws = WebServer(ring_size, path)
    scanner = ImageScanner(path, ws.ring_buffer)
    scanner.start_scanning()
    import signal

    def _handle_signals(signum, frame):
        scanner.stop_scanning()
        try:
            ws.shutdown()
        except Exception:
            pass

    signal.signal(signal.SIGINT, _handle_signals)
    signal.signal(signal.SIGTERM, _handle_signals)

    try:
        ws.run(host=host, port=port, debug=debug)
    finally:
        scanner.stop_scanning()