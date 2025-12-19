import os
import threading
from flask import Flask, render_template, jsonify, send_from_directory, url_for, request
from werkzeug.serving import make_server


class WebServer:
    def __init__(self, buffer_size, image_folder):
        here = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.abspath(os.path.join(here, '..', 'templates'))
        static_folder = os.path.abspath(os.path.join(here, '..', 'static'))

        self.app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
        self.image_folder = os.path.abspath(image_folder)

        # import here to avoid circular imports when module is used elsewhere
        from server.src.ring_buffer import RingBuffer

        self.ring_buffer = RingBuffer(buffer_size)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            images = self.ring_buffer.get_all()
            image_urls = [self._image_url(p) for p in images]
            return render_template('index.html', images=image_urls)

        @self.app.route('/api/images')
        def api_images():
            images = self.ring_buffer.get_all()
            image_urls = [self._image_url(p) for p in images]
            return jsonify(images=image_urls)

        @self.app.route('/monitored/<path:filename>')
        def monitored(filename):
            # Try to open the file as an image and apply auto-contrast before sending.
            import io
            import mimetypes
            try:
                from PIL import Image, ImageOps
            except Exception:
                # Pillow not available — fall back to sending raw file
                return send_from_directory(self.image_folder, filename)

            # Resolve the absolute path and prevent directory traversal
            full_path = os.path.abspath(os.path.join(self.image_folder, filename))
            if not full_path.startswith(self.image_folder):
                return ("Forbidden", 403)

            if not os.path.exists(full_path):
                return ("Not Found", 404)

            try:
                with Image.open(full_path) as img:
                    img = img.convert('RGB')
                    img = ImageOps.autocontrast(img, cutoff=.001)
                    buf = io.BytesIO()
                    # Prefer original format when available; default to JPEG
                    fmt = (img.format or 'JPEG')
                    # Pillow expects 'JPEG' rather than 'JPG'
                    if fmt.upper() == 'JPG':
                        fmt = 'JPEG'
                    img.save(buf, format=fmt)
                    buf.seek(0)
                    mime, _ = mimetypes.guess_type(full_path)
                    if not mime:
                        mime = 'image/jpeg'
                    return (buf.getvalue(), 200, {'Content-Type': mime})
            except OSError:
                # Not an image — fall back to original behavior
                return send_from_directory(self.image_folder, filename)

        @self.app.route('/__shutdown', methods=['POST'])
        def _shutdown():
            # Only allow local shutdowns (be permissive for empty/localhost addresses)
            remote = request.remote_addr or ''
            if not (remote.startswith('127.') or remote in ('127.0.0.1', '::1', 'localhost', '')):
                return ("Forbidden", 403)

            # If we have a managed http server, use its shutdown; otherwise try the werkzeug hook
            if getattr(self, '_http_server', None):
                try:
                    self._http_server.shutdown()
                except Exception:
                    pass
                return ("Shutting down", 200)

            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                # Last resort: force-exit in background so the response returns.
                def _exit():
                    os._exit(0)

                threading.Thread(target=_exit, daemon=True).start()
                return ("Shutting down (forced)", 200)
            func()
            return ("Shutting down", 200)

    def _image_url(self, path):
        """Return a URL for the given image path; if the image is inside monitored folder, return monitored URL."""
        try:
            rel = os.path.relpath(path, self.image_folder)
            if rel.startswith('..'):
                return path
            # url_for must be called during a request context; it's fine inside route handlers
            return url_for('monitored', filename=rel)
        except Exception:
            return path

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Start the WSGI server in a background thread and block until it's stopped.

        This uses Werkzeug's `make_server` to create a server object with a
        `shutdown()` method so callers can request a clean shutdown.
        """
        # Create server and serve in a background thread
        self._http_server = make_server(host, port, self.app)
        self._server_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._server_thread.start()

        try:
            # Block until the server thread ends (shutdown called)
            self._server_thread.join()
        except KeyboardInterrupt:
            # In case someone hits Ctrl-C, ensure shutdown is initiated
            try:
                self.shutdown()
            except Exception:
                pass

    def add_image(self, image_path):
        if os.path.exists(image_path):
            self.ring_buffer.add(image_path)

    def shutdown(self):
        """Shut down the running WSGI server if present.

        Returns True if shutdown was triggered, False otherwise.
        """
        if getattr(self, '_http_server', None):
            try:
                self._http_server.shutdown()
                # join the thread briefly
                if getattr(self, '_server_thread', None):
                    self._server_thread.join(timeout=3)
                return True
            except Exception:
                return False
        return False