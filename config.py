import json
import logging
import os

# Get a logger for this module
logger = logging.getLogger(__name__)

class Config:
    """
    Handles loading and accessing configuration settings from config.json.
    """
    def __init__(self, filename='config.json'):
        self.filename = filename
        self._config_data = {}
        self.load_config()

    def load_config(self):
        """Loads configuration from the JSON file."""
        if not os.path.exists(self.filename):
            logger.error(f"Config file not found: {self.filename}. Please create it in the same directory as main.py.")
            # Create a dummy config if it doesn't exist for initial run, then exit
            dummy_config = {
              "Server": {
                "host": "0.0.0.0",
                "port": 5000
              },
              "Arduino": {
                "expected_data_format": "JSON",
                "moisture_unit": "Analog (0-1023)"
              },
              "GUI": {
                "data_refresh_interval_ms": 2000,
                "log_display_limit": 50
              },
              "Irrigation": {
                "watering_duration_seconds": 5
              },
              "Sensors": [
                {
                  "name": "PlantA",
                  "moisture_threshold": 400,
                  "watering_relay_pin": 27,
                  "ip_address": "192.168.1.101"
                },
                {
                  "name": "PlantB",
                  "moisture_threshold": 350,
                  "watering_relay_pin": 26,
                  "ip_address": "192.168.1.102"
                }
              ],
              "Telegram": {
                "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
                "chat_id": "YOUR_CHAT_ID",
                "low_moisture_alert_interval_minutes": 60
              }
            }
            try:
                with open(self.filename, 'w') as f:
                    json.dump(dummy_config, f, indent=2)
                logger.info(f"Created a sample {self.filename}. Please review and update it.")
            except Exception as e:
                logger.error(f"Could not create sample config file: {e}")
            exit(1) # Exit after creating dummy config to prompt user to fill it

        try:
            with open(self.filename, 'r') as f:
                self._config_data = json.load(f)
            logger.info(f"Configuration loaded from {self.filename}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON in {self.filename}: {e}")
            exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred loading config: {e}")
            exit(1)

    def get(self, section, key, default=None):
        """Retrieves a setting from the config data."""
        return self._config_data.get(section, {}).get(key, default)

    def get_sensors_config(self):
        """Retrieves the list of sensor configurations."""
        return self._config_data.get('Sensors', [])

    def get_telegram_config(self):
        """Retrieves the Telegram configuration."""
        return self._config_data.get('Telegram', {})
