import json
import os
import threading

from flask import Flask

from telegram_notifier import TelegramNotifier
from logger import logger
from routes import register_routes


def main():
    with open('config.json', 'r') as f:
        config = json.load(f)
    app = Flask(__name__)
    register_routes(app,config)

    SERVER_HOST = config.get('Server', {}).get('host')
    SERVER_PORT = config.get('Server', {}).get('port')

    with open('config.json', 'r') as f:
        config = json.load(f)

    # Create a 'static' directory if it doesn't exist to serve dashboard.html
    if not os.path.exists('static'):
        os.makedirs('static')
        logger.info("Created 'static' directory.")

    telegram_notifier = TelegramNotifier(
        config.get('Telegram', 'bot_token'),
        config.get('Telegram', 'chat_id')
    )

    telegram_thread = threading.Thread(target=telegram_notifier.search_dry_plants, daemon=True)
    telegram_thread.start()

    logger.info(f"Starting Flask server on http://{SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False,
            use_reloader=False)  # use_reloader=False because of threading issues with Flask reloader


# --- Server Start ---
if __name__ == '__main__':
    main()
