import threading
import time
import logging
from main import DaggerheartBot
from webapp_server import run_webapp
from config import WEBAPP_URL, PORT

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    """Запуск бота и веб-сервера"""
    print("🚀 Запуск Daggerheart Bot...")
    print(f"📱 WEBAPP_URL: {WEBAPP_URL}")
    print(f"🌐 PORT: {PORT}")

    # Запуск веб-сервера в отдельном потоке
    webapp_thread = threading.Thread(target=run_webapp, daemon=True)
    webapp_thread.start()
    print("🌐 Веб-сервер запущен в фоновом режиме")

    # Задержка для запуска веб-сервера
    time.sleep(3)

    # Запуск бота
    print("🤖 Запуск Telegram бота...")
    bot = DaggerheartBot()
    bot.run()


if __name__ == "__main__":
    main()