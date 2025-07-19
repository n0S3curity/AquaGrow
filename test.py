import requests
import time

# Configuration for your Flask server
BASE_URL = "http://127.0.0.1:5000" # Default Flask development server address

def send_sensor_update(sensor_name, ip_address, moisture_value):
    """
    Sends a GET request to the /api/update endpoint to update sensor data.
    """
    endpoint = f"{BASE_URL}/api/update"
    params = {
        "name": sensor_name,
        "ip": ip_address,
        "moisture": moisture_value
    }

    print(f"Sending update request for sensor: {sensor_name} with moisture: {moisture_value}...")
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Successfully updated {sensor_name}. Server response: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the server at {BASE_URL}. Is the Flask app running?")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
    except Exception as err:
        print(f"An unexpected error occurred: {err}")

if __name__ == "__main__":
    # Example usage:
    # Make sure your Flask app (app.py from the previous response) is running
    # before you execute this script.

    # Update "Outside garden sensor" with new moisture data
    send_sensor_update("Outside garden sensor", "192.0.0.100", 777)
    time.sleep(1) # Wait a bit before sending another update

    # Update "Indoor plant A" with new moisture data
    send_sensor_update("Indoor plant A", "192.0.0.101", 720)
    time.sleep(1)
