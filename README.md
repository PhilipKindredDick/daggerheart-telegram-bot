🗡️ Daggerheart Telegram Bot
Telegram бот для игры в Daggerheart с ГМ на базе DeepSeek API и Telegram Mini Apps.
✨ Возможности

🎮 Создание персонажей через Mini App
🎲 Система бросков костей
🤖 ГМ на базе DeepSeek API
📱 Удобный интерфейс в Telegram
💾 Сохранение игровых сессий

🚀 Быстрый старт
1. Клонирование репозитория
bashgit clone https://github.com/your-username/daggerheart-telegram-bot.git
cd daggerheart-telegram-bot
2. Установка зависимостей
bashpip install -r requirements.txt
3. Настройка окружения
Создай файл .env по примеру .env.example:
envBOT_TOKEN=your_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
WEBAPP_URL=https://your-replit-url.repl.co
PORT=8080
4. Получение токенов
Telegram Bot Token

Напиши @BotFather в Telegram
Выполни команду /newbot
Следуй инструкциям
Скопируй полученный токен

DeepSeek API Key

Зайди на https://platform.deepseek.com/
Зарегистрируйся и получи API ключ
Скопируй ключ в .env

5. Запуск
bashpython run_bot.py
🔧 Деплой на Replit

Создай новый Repl (Python)
Импортируй проект из GitHub
Настрой переменные окружения в Secrets
Обнови WEBAPP_URL в настройках
Запусти проект

📁 Структура проекта
daggerheart-telegram-bot/
├── main.py                 # Основной файл бота
├── webapp_server.py        # Веб-сервер для Mini App
├── config.py              # Конфигурация
├── run_bot.py             # Скрипт запуска
├── requirements.txt       # Зависимости
├── .env.example          # Пример настроек
├── .replit               # Конфигурация Replit
├── game/                 # Игровая логика (в разработке)
│   ├── __init__.py
│   ├── game_session.py
│   ├── character.py
│   └── mechanics.py
└── deepseek/             # Интеграция с DeepSeek (в разработке)
    ├── __init__.py
    └── gm_api.py
🎮 Как играть

Запусти бота командой /start
Нажми "Начать игру" для открытия Mini App
Создай персонажа в веб-интерфейсе
Взаимодействуй с ГМ через чат

🛠️ Текущий статус

✅ Базовая структура бота
✅ Mini App интерфейс
✅ Создание персонажей
✅ Система бросков костей
🔄 Интеграция с DeepSeek API (в разработке)
🔄 Игровые механики Daggerheart (в разработке)
🔄 База данных для сохранения (в разработке)

📚 Ресурсы

Правила Daggerheart
Telegram Bot API
Telegram Mini Apps
DeepSeek API

🤝 Вклад в проект

Форкни репозиторий
Создай ветку для новой функции
Сделай коммит изменений
Отправь Pull Request

📝 Лицензия
MIT License
🐛 Баги и предложения
Создавай Issues в репозитории для багов и предложений.

Автор: Клава 🤖
Версия: 0.1.0 (MVP)