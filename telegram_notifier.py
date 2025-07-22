import json
import time
from datetime import datetime

from logger import logger


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.last_sent_message_time = None
        self.token = token
        self.chat_id = chat_id

    def send_message(self, message: str):
        import requests

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        print(url)
        response = requests.post(url, json=payload)
        logger.info(f"Telegram response: {response.status_code} - {response.text}")
        return "OK" if response.status_code == 200 else "Error"

    def search_dry_plants(self):
        try:
            while True:
                with open('sensors.json', 'r') as f:
                    all_sensors_data = json.load(f)  # Renamed to avoid confusion

                # Iterate over the items (key, value pairs) of the dictionary
                # key will be the sensor name (e.g., "OutsideGardenSensor")
                # sensor_details will be the dictionary containing ip, moisture, history
                for sensor_name, sensor_details in all_sensors_data.items():
                    # Access moisture from sensor_details
                    moisture_level = sensor_details.get('moisture')

                    logger.info(f"Checking sensor: {sensor_name} with moisture level {moisture_level}")

                    # Ensure moisture_level is not None and meets the threshold
                    if moisture_level is not None and moisture_level >= 700:
                        logger.info(f"Dry plant detected: {sensor_name} with moisture level {moisture_level}")
                        moist_percent = int(moisture_level / 1023 * 100)
                        message = f"Dry plant detected: {sensor_name} with moisture level {moisture_level}, {moist_percent}%"

                        # check if passed more than 8 HRS than the last message was sent, if yes send, if not , pass
                        if self.last_sent_message_time is None or (
                                datetime.now() - self.last_sent_message_time).total_seconds() > 8 * 3600:
                            res = self.send_message(message)
                            if res == "OK":
                                logger.info(f"Message sent successfully for {sensor_name}")
                                self.last_sent_message_time = datetime.now()
                            else:
                                logger.error(f"Failed to send message for {sensor_name}: {res}")
                        else:
                            logger.info(
                                f"Skipping message for {sensor_name} as it was sent recently. Last sent on {self.last_sent_message_time}")
                    else:
                        logger.info(
                            f"Sensor {sensor_name} is not dry or moisture data is missing (current moisture: {moisture_level}).")

                time.sleep(5)  # Wait 5 seconds before checking again

        except json.JSONDecodeError as jde:
            logger.error(f"Error decoding sensors.json: {jde}. Please check file format.")
            time.sleep(10)  # Wait before retrying after a JSON error
            self.search_dry_plants()  # Retry
        except FileNotFoundError:
            logger.error(f"sensors.json not found. Please ensure it's in the correct directory.")
            time.sleep(30)  # Wait longer if file is missing, assume it might appear
            self.search_dry_plants()  # Retry
        except Exception as e:
            logger.error(f"An unexpected error occurred in search_dry_plants: {e}")
            time.sleep(10)  # Wait before retrying after an general error
            self.search_dry_plants()  # Retry


if __name__ == '__main__':
    # Example usage
    with open('config.json', 'r') as f:
        config = json.load(f)

    notifier = TelegramNotifier(config['Telegram']['bot_token'], config['Telegram']['chat_id'])
    notifier.search_dry_plants()
