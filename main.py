import os
import threading

from flask import Flask

from telegram_notifier import TelegramNotifier
from config import Config
from logger import logger
from routes import register_routes


config_manager = Config()
app = Flask(__name__)
register_routes(app, config_manager)

SERVER_HOST = config_manager.get('Server', 'host', '0.0.0.0')
SERVER_PORT = config_manager.get('Server', 'port', 5000)
DATA_REFRESH_INTERVAL_MS = config_manager.get('GUI', 'data_refresh_interval_ms', 2000)

# --- Server Start ---
if __name__ == '__main__':
    # Create a 'static' directory if it doesn't exist to serve dashboard.html
    if not os.path.exists('static'):
        os.makedirs('static')
        logger.info("Created 'static' directory.")

    telegram_notifier = TelegramNotifier(
        config_manager.get('Telegram', 'bot_token'),
        config_manager.get('Telegram', 'chat_id')
    )

    telegram_thread = threading.Thread(target=telegram_notifier.search_dry_plants,daemon=True)
    telegram_thread.start()

    logger.info(f"Starting Flask server on http://{SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False,
            use_reloader=False)  # use_reloader=False because of threading issues with Flask reloader
