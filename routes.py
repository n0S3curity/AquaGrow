import json
import logging
import os
import random
import time
import requests

from flask import jsonify, request, send_from_directory

# Get a logger for this module
logger = logging.getLogger(__name__)


def register_routes(app, sensor_manager, config_manager):
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
        with open('sensors.json', 'r') as f:
            sensor_data = json.load(f)
        return jsonify(sensor_data)

    @app.route('/api/update', methods=['GET'])
    def update_sensor():
        logger.info(f"Received request to update sensor data:  {request.args}")
        new_data = {}
        # open sensor data file and update sensor data by name
        with open('sensors.json', 'r') as f:
            sensor_data = json.load(f)
            logger.info(f"sensors loaded: {sensor_data}")
        new_data['sensor_name'] = request.args.get('name')
        new_data['ip'] = request.args.get('ip')
        new_data['moisture'] = request.args.get('moisture', type=int)
        logger.info(f"sensor {new_data['sensor_name']} updating data:  {new_data}")
        # if not sensor_name or not ip or not moisture:
        #     return "missing params", 400
        sensor_data[new_data['sensor_name']] = {
            'ip': new_data['ip'],
            'moisture': new_data['moisture']
        }
        # write updated sensor data to file
        with open('sensors.json', 'w') as f:
            json.dump(sensor_data, f, indent=4)
            logger.info(f"sensors updated with new {sensor_data}")

        return "OK", 200

    # API endpoint to get status for a single sensor
    @app.route('/api/status/<string:sensor_name>', methods=['GET'])
    def get_single_sensor_status(sensor_name):
        data = sensor_manager.get_sensor_data(sensor_name)
        if data:
            return jsonify(data)
        else:
            logger.warning(f"Request for status of unknown sensor: {sensor_name}")
            return jsonify({"message": f"Sensor '{sensor_name}' not found"}), 404

    # API endpoint to water one or multiple sensors
    @app.route('/api/water', methods=['POST'])
    def water_sensors():
        data = request.get_json()
        sensor_names_to_water = data.get('sensor_names', [])  # Expect a list of sensor names

        if not sensor_names_to_water:
            logger.warning("Water request received with no sensor names.")
            return jsonify({"message": "No sensors specified for watering.", "status": "error"}), 400

        results = {}
        for name in sensor_names_to_water:
            sensor = sensor_manager.sensors.get(name)
            if sensor:
                logger.info(f"Attempting to water sensor: {name}")
                try:
                    # --- Actual Arduino watering logic (uncomment when ready) ---
                    # Ensure the Arduino is configured to listen for POST requests
                    # on its IP address and a specific endpoint, e.g., /water
                    # The Arduino would then activate the relay connected to 'watering_relay_pin'
                    # for 'WATERING_DURATION' seconds.

                    # if sensor.ip_address:
                    #     arduino_response = requests.post(
                    #         f"http://{sensor.ip_address}/water",
                    #         json={"duration": WATERING_DURATION, "pin": sensor.watering_relay_pin},
                    #         timeout=5
                    #     )
                    #     arduino_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                    #     results[name] = {"status": "success", "message": f"Watering command sent to {sensor.ip_address}"}
                    #     logger.info(f"Watering command sent to {name}. Arduino response: {arduino_response.text}")
                    # else:
                    #     results[name] = {"status": "error", "message": f"No IP address configured for {name}."}
                    #     logger.error(f"Watering for {name} failed: No IP address configured.")

                    # --- Simulation for development without real Arduino ---
                    time.sleep(1)  # Simulate network delay
                    if random.random() > 0.1:  # 90% success rate simulation
                        results[name] = {"status": "success", "message": f"Simulating watering for {name}"}
                        logger.info(f"Simulated watering for {name}.")
                    else:
                        results[name] = {"status": "error", "message": f"Simulated failure for {name}"}
                        logger.error(f"Simulated watering failure for {name}.")
                    # --- End Simulation ---

                except requests.exceptions.RequestException as e:
                    results[name] = {"status": "error", "message": f"Network error sending command to {name}: {e}"}
                    logger.error(f"Network error sending watering command to {name}: {e}")
                except Exception as e:
                    results[name] = {"status": "error", "message": f"Unexpected error watering {name}: {e}"}
                    logger.error(f"Unexpected error watering {name}: {e}")
            else:
                results[name] = {"status": "error", "message": f"Sensor '{name}' not found."}
                logger.warning(f"Watering requested for unknown sensor: {name}")

        return jsonify({"message": "Watering process initiated for selected sensors.", "results": results}), 200

    # API endpoint to get logs
    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        from logger import log_buffer  # Import log_buffer here to avoid circular dependency
        limit = request.args.get('limit', type=int, default=LOG_DISPLAY_LIMIT)
        logs = jsonify(list(log_buffer)[-limit:])
        print("Returning logs:", logs.response[0])  # Debug print to see logs being returned
        return logs

    # API endpoint for Arduino to report data
    @app.route('/arduino/data', methods=['POST'])
    def arduino_data():
        if request.is_json:
            data = request.get_json()
            sensor_name = data.get('sensor_name')
            moisture = data.get('moisture')

            if sensor_name and moisture is not None:
                try:
                    moisture_value = int(moisture)
                    if sensor_manager.update_sensor_moisture(sensor_name, moisture_value):
                        logger.info(f"Arduino reported data for {sensor_name}: {moisture_value}")
                        return jsonify({"message": "Data received", "status": "success"}), 200
                    else:
                        return jsonify({"message": f"Sensor '{sensor_name}' not configured", "status": "error"}), 404
                except ValueError:
                    logger.error(f"Invalid moisture value received from Arduino for {sensor_name}: {moisture}")
                    return jsonify({"message": "Invalid moisture value", "status": "error"}), 400
            else:
                logger.warning("Arduino data missing 'sensor_name' or 'moisture' key.")
                return jsonify({"message": "Missing 'sensor_name' or 'moisture' data", "status": "error"}), 400
        else:
            logger.warning("Arduino data not in JSON format.")
            return jsonify({"message": "Request must be JSON", "status": "error"}), 400
