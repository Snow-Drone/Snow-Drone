# Local Image Server

This project is a simple web server that hosts a website available on the local network. It scans a specified folder for newly added images, adds them to a ring buffer, and displays the new image along with all other images in that buffer.

## Project Structure

```
local-image-server
├── src
│   ├── main.py          # Entry point of the application
│   ├── server.py        # Web server setup and routing
│   ├── scanner.py       # Monitors folder for new images
│   ├── ring_buffer.py    # Implements a circular buffer for images
│   ├── config.py        # Configuration settings
│   └── utils.py         # Utility functions for image processing
├── templates
│   └── index.html       # HTML template for displaying images
├── static
│   ├── css
│   │   └── styles.css   # CSS styles for the web application
│   └── js
│       └── app.js       # JavaScript for dynamic interactions
├── monitored_images      # Folder for storing monitored images
├── tests
│   └── test_ring_buffer.py # Unit tests for the RingBuffer class
├── requirements.txt      # Project dependencies
├── .env                  # Environment variables
└── README.md             # Project documentation
```

## Setup Instructions

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Configure the environment variables in the `.env` file as needed.
6. Place images in the `monitored_images` folder for the server to scan.
7. Run the application:
   ```
   python src/main.py --ring_size 10
   ```
8. Access the web server in your browser at `http://localhost:5000`.

### CLI options

The server accepts a few command-line options:

- `--host` : host to bind to (default `0.0.0.0`)
- `--port` : port to listen on (default `5000`)
- `--debug` : run in debug mode
- `--ring_size` : size of the in-memory ring buffer for recent images (must be a positive integer)

Example:

```
python src/main.py --port 5001 --ring_size 20
```

## Usage

Once the server is running, it will automatically scan the `monitored_images` folder for new images. The images will be displayed on the web page, and the most recent images will be shown alongside the older ones, managed by the ring buffer.
