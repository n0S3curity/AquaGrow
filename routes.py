import datetime
import json
import logging
import os
import random
import time
import requests

from flask import jsonify, request, send_from_directory

# Get a logger for this module
logger = logging.getLogger(__name__)


def register_routes(app, config_manager):
    """
    Registers all Flask routes with the given app instance.
    """

    SERVER_HOST = config_manager.get('Server', 'host', '0.0.0.0')
    SERVER_PORT = config_manager.get('Server', 'port', 5000)
    WATERING_DURATION = config_manager.get('Irrigation', 'watering_duration_seconds', 5)
    LOG_DISPLAY_LIMIT = config_manager.get('GUI', 'log_display_limit', 50)

    # Serve the main dashboard HTML file
    @app.route('/')
    def index():
        try:
            # Assuming dashboard.html is in the 'static' folder
            return send_from_directory('templates', 'dash.html')
        except Exception as e:
            logger.error(f"Error serving dashboard.html: {e}")
            return "Error loading dashboard", 500

    # API endpoint to get status for all sensors
    @app.route('/api/status', methods=['GET'])
    def get_all_sensor_status():
        try:
            with open('sensors.json', 'r') as f:
                sensor_data = json.load(f)
            return jsonify(sensor_data), 200
        except FileNotFoundError:
            return jsonify({}), 200
        except json.JSONDecodeError:
            return jsonify({}), 500  # Or handle more gracefully

    @app.route('/api/update', methods=['GET'])
    def update_sensor():
        logger.info(f"Received request to update sensor data: {request.args}")

        sensor_name = request.args.get('name')
        ip = request.args.get('ip')
        moisture = request.args.get('moisture', type=int)

        if not all([sensor_name, ip, moisture is not None]):
            return "Missing parameters (name, ip, moisture)", 400

        logger.info(f"Sensor {sensor_name} updating data: Name={sensor_name}, IP={ip}, Moisture={moisture}")

        try:
            # Open sensor data file
            with open('sensors.json', 'r') as f:
                sensor_data = json.load(f)
                # logger.info(f"Sensors loaded: {sensor_data}")
        except FileNotFoundError:
            sensor_data = {}
            logger.info("sensors.json not found, initializing with empty data.")
        except json.JSONDecodeError:
            sensor_data = {}
            logger.warning("sensors.json is empty or malformed, initializing with empty data.")

        # Get current sensor data or initialize if new
        current_sensor_info = sensor_data.get(sensor_name, {})

        # Update IP and current moisture
        current_sensor_info['ip'] = ip
        current_sensor_info['moisture'] = moisture

        # Prepare history entry
        # Use ISO format for timestamp to be easily parsed by JavaScript Date object
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        new_history_entry = {"timestamp": timestamp, "moisture": moisture}

        # Retrieve existing history or create a new list
        history = current_sensor_info.get('history', [])

        # Append new moisture reading to history
        history.append(new_history_entry)

        # Store history back
        current_sensor_info['history'] = history

        # Update the main sensor_data dictionary
        sensor_data[sensor_name] = current_sensor_info

        # Write updated sensor data to file
        with open('sensors.json', 'w') as f:
            json.dump(sensor_data, f, indent=4)
            # logger.info(f"Sensors updated with new data for {sensor_name}: {sensor_data[sensor_name]}")

        return "OK", 200

    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        from logger import log_buffer  # Import log_buffer here to avoid circular dependency
        limit = request.args.get('limit', type=int, default=LOG_DISPLAY_LIMIT)
        logs = jsonify(list(log_buffer)[-limit:])
        # print("Returning logs:", logs.response[0])  # Debug print to see logs being returned
        return logs

