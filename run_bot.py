import threading
import time
import logging
from main import DaggerheartBot
from webapp_server import run_webapp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    """Запуск бота и веб-сервера"""
    print("🚀 Запуск Daggerheart Bot...")

    # Запуск веб-сервера в отдельном потоке
    webapp_thread = threading.Thread(target=run_webapp, daemon=True)
    webapp_thread.start()

    # Небольшая задержка для запуска веб-сервера
    time.sleep(2)

    # Запуск бота
    bot = DaggerheartBot()
    bot.run()


if __name__ == "__main__":
    main()