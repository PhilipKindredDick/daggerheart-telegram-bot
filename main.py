import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import os
from config import BOT_TOKEN, WEBAPP_URL

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class DaggerheartBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("game", self.start_game))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = f"""
🗡️ Добро пожаловать в Daggerheart Bot, {user.first_name}!

Я помогу тебе играть в Daggerheart с ГМ на базе ИИ.

Команды:
/game - Начать новую игру
/help - Помощь

Готов к приключениям? 🎲
        """

        keyboard = [
            [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")],
            [InlineKeyboardButton("📚 Правила", url="https://ru.daggerheart.su/rule")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 Помощь по боту Daggerheart

🎮 Основные команды:
/start - Начать работу с ботом
/game - Запустить игровую сессию
/help - Показать эту справку

🎲 Как играть:
1. Нажми /game или кнопку "Начать игру"
2. Создай персонажа в веб-интерфейсе
3. Взаимодействуй с ГМ через чат

📚 Правила игры: https://ru.daggerheart.su/rule
        """
        await update.message.reply_text(help_text)

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск игровой сессии"""
        logger.info(f"Открытие игры для пользователя {update.effective_user.id}")
        logger.info(f"WEBAPP_URL: {WEBAPP_URL}")

        keyboard = [
            [InlineKeyboardButton(
                "🎮 Открыть игру",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        game_text = """
🎮 Игровая сессия Daggerheart

Нажми кнопку ниже, чтобы открыть игровой интерфейс.
В нем ты сможешь:
- Создать персонажа
- Взаимодействовать с ГМ
- Использовать игровые механики

Удачи в приключениях! 🗡️
        """

        await update.message.reply_text(game_text, reply_markup=reply_markup)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        # Пока что просто эхо
        user_message = update.message.text

        # Здесь будет логика обработки игровых команд
        response = f"Получил сообщение: {user_message}\n\n(Пока что это заглушка, скоро здесь будет ГМ!)"

        await update.message.reply_text(response)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error(f"Update {update} caused error {context.error}")

    def run(self):
        """Запуск бота"""
        logger.info("Запуск Daggerheart Bot...")
        self.application.add_error_handler(self.error_handler)
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = DaggerheartBot()
    bot.run()