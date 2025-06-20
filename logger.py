import logging
from datetime import datetime
from collections import deque

# --- Global Logger Setup ---
MAX_LOG_ENTRIES = 200 # Max number of log entries to keep in memory
log_buffer = deque(maxlen=MAX_LOG_ENTRIES)

class FlaskStreamHandler(logging.Handler):
    """
    Custom logging handler to push log messages to a deque for web display.
    """
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "message": self.format(record)
        }
        log_buffer.append(log_entry)

def setup_global_logging():
    """Sets up basic logging to console, file, and the log_buffer."""
    # Ensure handlers are not duplicated on re-runs or multiple imports
    root_logger = logging.getLogger()
    if not root_logger.handlers: # Only add handlers if none exist
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(), # Console output
                logging.FileHandler("plant_monitor.log") # File output
            ]
        )
        # Add custom handler for web UI
        web_handler = FlaskStreamHandler()
        web_handler.setLevel(logging.INFO)
        root_logger.addHandler(web_handler)
        root_logger.info("Global logging initialized.")
    else:
        root_logger.debug("Logging already set up.")

# Call setup_global_logging immediately when this module is imported
setup_global_logging()

# Get a logger instance for other modules to use
# This ensures all log messages go through the configured handlers
logger = logging.getLogger(__name__) # Logger for this specific module
