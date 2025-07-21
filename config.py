import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Веб-приложение
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-replit-url.replit.dev")
if WEBAPP_URL == "https://your-replit-url.replit.dev":
    print("⚠️ ВНИМАНИЕ: WEBAPP_URL не настроен!")
    print("Добавь правильный URL в Secrets на Replit")
PORT = int(os.getenv("PORT", 8080))

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///daggerheart.db")

# Настройки игры
GAME_SETTINGS = {
    "max_players": 6,
    "session_timeout": 3600,  # 1 час в секундах
    "default_language": "ru"
}

# Настройки DeepSeek ГМ
GM_SETTINGS = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": """
Ты - Гейммастер в игре Daggerheart. Твоя задача:
1. Создавать увлекательные приключения
2. Следовать правилам игры
3. Быть справедливым и интересным
4. Отвечать на русском языке
5. Использовать игровые механики системы

Помни: ты создаешь историю вместе с игроками!
"""
}