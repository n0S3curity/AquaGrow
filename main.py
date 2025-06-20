import os
import threading
import time
import random

from flask import Flask

# Import your custom modules
from config import Config
from logger import setup_global_logging, logger # Import logger from logger.py
from sensor import SensorDataManager
from routes import register_routes # Import the function to register routes

# Ensure global logging is set up at the very beginning
# setup_global_logging() # This is now called directly in logger.py when imported

# Initialize configuration
config_manager = Config()

# Initialize sensor data manager
sensor_manager = SensorDataManager(config_manager)

# Flask App Setup
app = Flask(__name__)
app.config['DEBUG'] = True # For development, set to False in production

# Register all routes from the routes module
register_routes(app, sensor_manager, config_manager)

# Get server host and port from config
SERVER_HOST = config_manager.get('Server', 'host', '0.0.0.0')
SERVER_PORT = config_manager.get('Server', 'port', 5000)
DATA_REFRESH_INTERVAL_MS = config_manager.get('GUI', 'data_refresh_interval_ms', 2000)

# --- Background Sensor Data Simulation (for multiple sensors) ---
def simulate_sensor_data(sensor_data_manager, refresh_interval_ms):
    """
    Simulates incoming sensor data for all configured sensors.
    In a real scenario, this would be replaced by actual data reception
    from the Arduino via WiFi for each sensor.
    """
    logger.info("Starting multi-sensor data simulation thread...")
    # Initialize random starting moisture for each sensor
    simulated_moisture = {name: random.randint(200, 800) for name in sensor_data_manager.sensors.keys()}

    while True:
        for sensor_name in sensor_data_manager.sensors.keys():
            # Simulate slight variations
            change = random.randint(-20, 20)
            simulated_moisture[sensor_name] = max(0, min(1023, simulated_moisture[sensor_name] + change))
            ip = '192.168.0.' + str(random.randint(1, 254))  # Simulate IP address for each sensor
            sensor_data_manager.update_sensor_moisture(sensor_name, simulated_moisture[sensor_name],ip)
        time.sleep(refresh_interval_ms / 1000.0)

# --- Server Start ---
if __name__ == '__main__':
    # Create a 'static' directory if it doesn't exist to serve dashboard.html
    if not os.path.exists('static'):
        os.makedirs('static')
        logger.info("Created 'static' directory.")

    # Start the multi-sensor data simulation thread
    # Only start if there are sensors configured
    if sensor_manager.sensors:
        simulation_thread = threading.Thread(
            target=simulate_sensor_data,
            args=(sensor_manager, DATA_REFRESH_INTERVAL_MS),
            daemon=True # Daemon threads exit when the main program exits
        )
        simulation_thread.start()
        logger.info("Multi-sensor data simulation thread started.")
    else:
        logger.warning("No sensors configured. Skipping simulation thread.")


    logger.info(f"Starting Flask server on http://{SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=app.config['DEBUG'], use_reloader=False) # use_reloader=False because of threading issues with Flask reloader
