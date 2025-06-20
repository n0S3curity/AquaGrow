from collections import deque
from datetime import datetime
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

class Sensor:
    """
    Represents a single moisture sensor and its associated plant/pump.
    Manages its current state and historical data.
    """
    def __init__(self, name, moisture_threshold, watering_relay_pin, ip_address):
        self.name = name
        self.current_moisture = "N/A"
        self.last_updated = None
        self.status = "Initializing..."
        self.moisture_threshold = moisture_threshold
        self.watering_relay_pin = watering_relay_pin
        self.ip_address = ip_address
        self.moisture_history = deque(maxlen=50) # Store last 50 readings for this sensor

    def update_moisture(self, value):
        """Updates the current moisture level and status for this sensor."""
        self.current_moisture = value
        self.last_updated = datetime.now().isoformat()
        self.moisture_history.append({"timestamp": self.last_updated, "value": value})

        if isinstance(value, (int, float)):
            if value < self.moisture_threshold:
                self.status = "DRY - Needs Water!"
                logger.warning(f"{self.name}: Moisture level ({value}) is below threshold ({self.moisture_threshold}).")
            else:
                self.status = "Optimal"
        else:
            self.status = "Invalid Data"
        logger.debug(f"{self.name}: Moisture updated: {self.current_moisture}, Status: {self.status}")

    def get_data(self):
        """Returns all data for this sensor."""
        return {
            "name": self.name,
            "current_moisture": self.current_moisture,
            "last_updated": self.last_updated,
            "status": self.status,
            "moisture_threshold": self.moisture_threshold,
            "watering_relay_pin": self.watering_relay_pin,
            "ip_address": self.ip_address,
            "moisture_history": list(self.moisture_history)
        }

class SensorDataManager:
    """
    Manages all configured sensors.
    """
    def __init__(self, config_manager):
        self.config = config_manager
        self.sensors = {} # Dictionary to hold Sensor objects, keyed by name
        self.load_sensors_from_config()
        logger.info("SensorDataManager initialized for multiple sensors.")

    def load_sensors_from_config(self):
        """Initializes Sensor objects based on config.json."""
        sensors_config = self.config.get_sensors_config()
        if not sensors_config:
            logger.warning("No sensors configured in config.json. Please add them.")
            return

        for s_config in sensors_config:
            name = s_config.get('name')
            if name:
                self.sensors[name] = Sensor(
                    name=name,
                    moisture_threshold=s_config.get('moisture_threshold', 400), # Default if not specified
                    watering_relay_pin=s_config.get('watering_relay_pin'),
                    ip_address=s_config.get('ip_address')
                )
                logger.info(f"Initialized sensor: {name}")
            else:
                logger.error(f"Sensor configuration missing 'name': {s_config}")

    def update_sensor_moisture(self, sensor_name, moisture_value):
        """Updates moisture for a specific sensor."""
        sensor = self.sensors.get(sensor_name)
        if sensor:
            sensor.update_moisture(moisture_value)
            return True
        else:
            logger.warning(f"Attempted to update unknown sensor: {sensor_name}")
            return False

    def get_all_sensors_data(self):
        """Returns data for all managed sensors."""
        return [sensor.get_data() for sensor in self.sensors.values()]

    def get_sensor_data(self, sensor_name):
        """Returns data for a single sensor."""
        sensor = self.sensors.get(sensor_name)
        return sensor.get_data() if sensor else None
