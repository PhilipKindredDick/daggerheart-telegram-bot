import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import json
import os
from config import BOT_TOKEN, WEBAPP_URL

# Импорты игровой механики
from game.game_session import session_manager, GameSession, SceneType
from game.character import Character, create_starting_character
from deepseek.gm_api import process_gm_action, start_new_scene

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

        # Хранилище пользовательских данных
        self.user_sessions = {}  # user_id -> session_id
        self.user_characters = {}  # user_id -> Character

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("game", self.start_game))
        self.application.add_handler(CommandHandler("session", self.session_info))
        self.application.add_handler(CommandHandler("roll", self.roll_dice))
        self.application.add_handler(CommandHandler("character", self.character_info))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = f"""
🗡️ Добро пожаловать в Daggerheart Bot, {user.first_name}!

Я помогу тебе играть в Daggerheart с ИИ Гейммастером на базе DeepSeek.

🎮 Основные команды:
/game - Начать новую игру или продолжить
/character - Информация о персонаже
/session - Статус игровой сессии
/roll - Бросить кости
/help - Подробная помощь

Готов к приключениям? 🎲
        """

        keyboard = [
            [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")],
            [InlineKeyboardButton("🎯 Открыть Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("📚 Правила", url="https://ru.daggerheart.su/rule")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 Подробная помощь по Daggerheart Bot

🎮 **Основные команды:**
/start - Главное меню
/game - Управление игрой
/character - Информация о персонаже
/session - Статус сессии
/roll [характеристика] - Бросок костей

🎲 **Броски костей:**
/roll strength - Бросок силы
/roll agility - Бросок ловкости
/roll finesse - Бросок точности
/roll instinct - Бросок интуиции
/roll presence - Бросок присутствия
/roll knowledge - Бросок знаний

🎭 **Как играть:**
1. Создай персонажа в Mini App
2. Пиши свои действия обычными сообщениями
3. ИИ Гейммастер отреагирует на твои действия
4. Используй /roll когда нужны проверки
5. Следи за Hope и Fear

📚 **Правила:** https://ru.daggerheart.su/rule
🐛 **Проблемы?** Напиши @support или попробуй /start
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        if query.data == "start_game":
            await self.start_game(update, context)

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск игровой сессии"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name

        logger.info(f"🎮 Запуск игры для {user_name} (ID: {user_id})")

        # Проверяем, есть ли уже персонаж
        if user_id not in self.user_characters:
            game_text = """
🎮 **Создание персонажа**

У тебя еще нет персонажа! Нажми кнопку ниже, чтобы открыть создание персонажа в Mini App.

В интерфейсе ты сможешь:
✨ Выбрать класс и происхождение
🎯 Распределить характеристики
⚔️ Получить стартовое снаряжение
🃏 Выбрать способности

После создания персонажа возвращайся сюда!
            """

            keyboard = [
                [InlineKeyboardButton("🎨 Создать персонажа", web_app=WebAppInfo(url=WEBAPP_URL))],
                [InlineKeyboardButton("📖 Правила создания", url="https://ru.daggerheart.su/rule")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.edit_message_text(game_text, reply_markup=reply_markup,
                                                              parse_mode='Markdown')
            else:
                await update.message.reply_text(game_text, reply_markup=reply_markup, parse_mode='Markdown')
            return

        # Есть персонаж, проверяем сессию
        character = self.user_characters[user_id]
        session_id = self.user_sessions.get(user_id)

        if not session_id:
            # Создаем новую сессию
            session_id = session_manager.create_session(user_id, f"Приключение {character.name}")
            session = session_manager.get_session(session_id)
            session.add_player(user_id, character)
            session.start_session()
            self.user_sessions[user_id] = session_id

            logger.info(f"✨ Создана новая сессия {session_id} для {user_name}")

            # Генерируем начальную сцену
            try:
                scene_description = await start_new_scene(session_id, "exploration", "начальная локация")

                game_text = f"""
🎭 **Игра началась!**

**Твой персонаж:** {character.name}
**Класс:** {character.character_class.name_ru if character.character_class else 'Неизвестно'}
**Происхождение:** {character.ancestry.name_ru if character.ancestry else 'Неизвестно'}

---

{scene_description}

---

💫 **Hope:** {character.progress.hope}/{character.progress.max_hope}
❤️ **Хиты:** {character.current_hp}/{character.hit_points}

*Опиши, что хочешь сделать! ИИ Гейммастер среагирует на твои действия.*
                """

            except Exception as e:
                logger.error(f"Ошибка генерации сцены: {e}")
                game_text = f"""
🎭 **Игра началась!**

**Твой персонаж:** {character.name}

Твое приключение начинается... (Гейммастер готовится)
Опиши, что хочешь сделать!
                """

        else:
            # Продолжаем существующую сессию
            session = session_manager.get_session(session_id)
            if session:
                status = session.get_session_status()
                recent_events = session.get_recent_events(3)

                events_text = "\n".join([f"• {event['description']}" for event in
                                         recent_events]) if recent_events else "Пока событий не было"

                game_text = f"""
🎭 **Продолжение игры**

**Персонаж:** {character.name}
**Сессия:** {status['name']}
**Сцена:** {status['current_scene']['description'] if status['current_scene'] else 'Неизвестно'}

📜 **Недавние события:**
{events_text}

💫 **Hope:** {status['global_hope']} | ⚡ **Fear:** {status['global_fear']}
❤️ **Хиты:** {character.current_hp}/{character.hit_points}

*Что дальше?*
                """
            else:
                game_text = "❌ Ошибка: сессия не найдена. Попробуй /start"

        keyboard = [
            [InlineKeyboardButton("🎲 Бросить кости", callback_data="quick_roll")],
            [InlineKeyboardButton("📊 Статус сессии", callback_data="session_status")],
            [InlineKeyboardButton("🎨 Редактировать персонажа", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(game_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(game_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def session_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о текущей сессии"""
        user_id = str(update.effective_user.id)
        session_id = self.user_sessions.get(user_id)

        if not session_id:
            await update.message.reply_text("❌ У тебя нет активной игровой сессии. Используй /game для начала игры.")
            return

        session = session_manager.get_session(session_id)
        if not session:
            await update.message.reply_text("❌ Сессия не найдена. Попробуй начать новую игру с /game")
            return

        status = session.get_session_status()
        recent_events = session.get_recent_events(5)

        # Форматируем информацию о сессии
        session_text = f"""
📊 **Статус игровой сессии**

🎭 **Сессия:** {status['name']}
🕐 **Время игры:** {status['uptime']}
👥 **Игроков:** {status['players_count']}/{status['max_players']}

💫 **Hope пулл:** {status['global_hope']}
⚡ **Fear пулл:** {status['global_fear']}

🎬 **Текущая сцена:**
{status['current_scene']['description'] if status['current_scene'] else 'Нет активной сцены'}

👥 **Персонажи:**
"""

        for char_info in status['characters']:
            current_marker = "👑 " if char_info['is_current_turn'] else "• "
            session_text += f"{current_marker}{char_info['name']} ({char_info['class']}) - {char_info['hp']} ❤️\n"

        if recent_events:
            session_text += f"\n📜 **Недавние события:**\n"
            for event in recent_events:
                session_text += f"• {event['description']}\n"

        await update.message.reply_text(session_text, parse_mode='Markdown')

    async def roll_dice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Бросок костей"""
        user_id = str(update.effective_user.id)

        # Проверяем, есть ли персонаж и сессия
        if user_id not in self.user_characters:
            await update.message.reply_text("❌ У тебя нет персонажа! Используй /game для создания.")
            return

        session_id = self.user_sessions.get(user_id)
        if not session_id:
            await update.message.reply_text("❌ У тебя нет активной сессии! Используй /game для начала игры.")
            return

        session = session_manager.get_session(session_id)
        if not session:
            await update.message.reply_text("❌ Сессия не найдена.")
            return

        # Парсим аргументы команды
        args = context.args
        if not args:
            # Показываем меню выбора характеристики
            keyboard = [
                [InlineKeyboardButton("💪 Сила", callback_data="roll_strength"),
                 InlineKeyboardButton("🤸 Ловкость", callback_data="roll_agility")],
                [InlineKeyboardButton("🎯 Точность", callback_data="roll_finesse"),
                 InlineKeyboardButton("👁️ Интуиция", callback_data="roll_instinct")],
                [InlineKeyboardButton("👑 Присутствие", callback_data="roll_presence"),
                 InlineKeyboardButton("📚 Знания", callback_data="roll_knowledge")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "🎲 **Выбери характеристику для броска:**\n\n"
                "Или используй: `/roll [характеристика]`\n"
                "Например: `/roll strength`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return

        trait_name = args[0].lower()
        difficulty = int(args[1]) if len(args) > 1 else 12

        # Проверяем валидность характеристики
        valid_traits = ['strength', 'agility', 'finesse', 'instinct', 'presence', 'knowledge']
        trait_names_ru = {
            'strength': 'сила', 'agility': 'ловкость', 'finesse': 'точность',
            'instinct': 'интуиция', 'presence': 'присутствие', 'knowledge': 'знания'
        }

        if trait_name not in valid_traits:
            await update.message.reply_text(
                f"❌ Неизвестная характеристика: {trait_name}\n"
                f"Доступные: {', '.join(valid_traits)}"
            )
            return

        # Совершаем бросок
        result = session.make_character_roll(user_id, trait_name, difficulty)

        if 'error' in result:
            await update.message.reply_text(f"❌ Ошибка: {result['error']}")
            return

        # Форматируем результат
        trait_ru = trait_names_ru.get(trait_name, trait_name)
        roll_text = f"🎲 **Бросок {trait_ru}**\n\n{result['formatted_result']}"

        await update.message.reply_text(roll_text, parse_mode='Markdown')

    async def character_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о персонаже"""
        user_id = str(update.effective_user.id)

        if user_id not in self.user_characters:
            await update.message.reply_text("❌ У тебя нет персонажа! Используй /game для создания.")
            return

        character = self.user_characters[user_id]
        char_sheet = character.get_character_sheet()

        char_text = f"""
👤 **{char_sheet['basic_info']['name']}**

🏛️ **Класс:** {char_sheet['basic_info']['class']}
🧬 **Происхождение:** {char_sheet['basic_info']['ancestry']}
📈 **Уровень:** {char_sheet['basic_info']['level']}

💪 **Характеристики:**
• Сила: {char_sheet['traits']['strength']:+d}
• Ловкость: {char_sheet['traits']['agility']:+d}
• Точность: {char_sheet['traits']['finesse']:+d}
• Интуиция: {char_sheet['traits']['instinct']:+d}
• Присутствие: {char_sheet['traits']['presence']:+d}
• Знания: {char_sheet['traits']['knowledge']:+d}

⚔️ **Боевые характеристики:**
• Хиты: {char_sheet['combat_stats']['hit_points']}
• Уклонение: {char_sheet['combat_stats']['evasion']}
• Порог урона: {char_sheet['combat_stats']['damage_threshold']}

💫 **Прогресс:**
• Hope: {char_sheet['progress']['hope']}
• Опыт: {char_sheet['progress']['experience']}

🎒 **Снаряжение:**
{chr(10).join([f"• {item}" for item in char_sheet['equipment']]) if char_sheet['equipment'] else "Пусто"}

🃏 **Способности:**
{chr(10).join([f"• {card}" for card in char_sheet['domain_cards']]) if char_sheet['domain_cards'] else "Нет"}
        """

        keyboard = [
            [InlineKeyboardButton("🎨 Редактировать", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("🎲 Бросить кости", callback_data="quick_roll")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(char_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений - взаимодействие с ГМ"""
        user_id = str(update.effective_user.id)
        user_message = update.message.text

        # Проверяем, есть ли персонаж и сессия
        if user_id not in self.user_characters:
            await update.message.reply_text(
                "🎭 Чтобы играть, сначала создай персонажа!\n"
                "Используй /game для начала."
            )
            return

        session_id = self.user_sessions.get(user_id)
        if not session_id:
            await update.message.reply_text(
                "🎭 У тебя нет активной игровой сессии!\n"
                "Используй /game для начала игры."
            )
            return

        # Показываем индикатор печати
        await update.message.chat.send_action("typing")

        try:
            # Отправляем действие ИИ Гейммастеру
            logger.info(f"🎭 Действие игрока {user_id}: {user_message}")

            gm_result = await process_gm_action(session_id, user_id, user_message)

            if gm_result.get("success"):
                gm_response = gm_result["gm_response"]

                # Добавляем контекстную информацию
                context_info = gm_result.get("context", {})
                if context_info:
                    hope = context_info.get("hope", 0)
                    fear = context_info.get("fear", 0)
                    gm_response += f"\n\n💫 Hope: {hope} | ⚡ Fear: {fear}"

                # Проверяем, нужны ли дополнительные кнопки
                effects = gm_result.get("effects", [])
                keyboard = []

                for effect in effects:
                    if effect.get("type") == "request_roll":
                        trait = effect.get("trait", "strength")
                        difficulty = effect.get("difficulty", 12)
                        keyboard.append([InlineKeyboardButton(
                            f"🎲 Бросить {trait} ({difficulty})",
                            callback_data=f"roll_{trait}_{difficulty}"
                        )])

                # Всегда добавляем общие кнопки
                keyboard.extend([
                    [InlineKeyboardButton("🎲 Бросок", callback_data="quick_roll"),
                     InlineKeyboardButton("📊 Статус", callback_data="session_status")]
                ])

                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

                await update.message.reply_text(gm_response, reply_markup=reply_markup)

            else:
                # Ошибка ИИ - используем запасной ответ
                fallback = gm_result.get("fallback_response", "ГМ временно недоступен...")
                await update.message.reply_text(f"🎭 {fallback}")

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "🎭 Что-то пошло не так... ГМ задумался.\n"
                "Попробуй еще раз или используй /help"
            )

    async def handle_web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных из Mini App"""
        user_id = str(update.effective_user.id)

        try:
            data = json.loads(update.message.web_app_data.data)
            action = data.get("action")

            if action == "character_created":
                # Создание персонажа
                char_data = data.get("character", {})

                # Создаем персонажа
                traits = {
                    "agility": char_data.get("agility", 0),
                    "strength": char_data.get("strength", 0),
                    "finesse": char_data.get("finesse", 0),
                    "instinct": char_data.get("instinct", 0),
                    "presence": char_data.get("presence", 0),
                    "knowledge": char_data.get("knowledge", 0)
                }

                character = create_starting_character(
                    char_data.get("name", "Безымянный"),
                    user_id,
                    char_data.get("class", "warrior"),
                    char_data.get("ancestry", "human"),
                    traits
                )

                self.user_characters[user_id] = character

                await update.message.reply_text(
                    f"✨ Персонаж **{character.name}** создан!\n"
                    f"Класс: {character.character_class.name_ru}\n"
                    f"Происхождение: {character.ancestry.name_ru}\n\n"
                    f"Теперь используй /game для начала приключения!",
                    parse_mode='Markdown'
                )

            elif action == "game_action":
                # Игровое действие из Mini App
                action_text = data.get("text", "")
                if action_text:
                    # Обрабатываем как обычное сообщение
                    update.message.text = action_text
                    await self.handle_message(update, context)

        except Exception as e:
            logger.error(f"Ошибка обработки Web App данных: {e}")
            await update.message.reply_text("❌ Ошибка обработки данных из Mini App")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error(f"Update {update} caused error {context.error}")

        if update.message:
            await update.message.reply_text(
                "🤖 Произошла техническая ошибка.\n"
                "Попробуй /start или обратись к администратору."
            )

    def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск Daggerheart Bot...")
        self.application.add_error_handler(self.error_handler)
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = DaggerheartBot()
    bot.run()
    import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
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
            [InlineKeyboardButton("🎯 Открыть Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
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

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        if query.data == "start_game":
            # Переадресуем на команду /game
            await self.start_game(update, context)

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск игровой сессии"""
        user_id = update.effective_user.id
        logger.info(f"🎮 Открытие игры для пользователя {user_id}")
        logger.info(f"📱 Используемый WEBAPP_URL: {WEBAPP_URL}")

        # Проверяем URL
        if "your-replit" in WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
            error_msg = f"❌ Неправильный WEBAPP_URL: {WEBAPP_URL}"
            logger.error(error_msg)
            await update.message.reply_text(
                "❌ Ошибка конфигурации бота!\n"
                "Администратор должен настроить WEBAPP_URL в переменных окружения."
            )
            return

        try:
            keyboard = [
                [InlineKeyboardButton(
                    "🎮 Открыть игру",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            logger.info(f"✅ Кнопка Mini App создана с URL: {WEBAPP_URL}")
        except Exception as e:
            logger.error(f"❌ Ошибка создания кнопки Mini App: {e}")
            await update.message.reply_text("❌ Ошибка создания игрового интерфейса!")
            return

        game_text = """
🎮 Игровая сессия Daggerheart

Нажми кнопку ниже, чтобы открыть игровой интерфейс.
В нем ты сможешь:
- Создать персонажа
- Взаимодействовать с ГМ
- Использовать игровые механики

Удачи в приключениях! 🗡️
        """

        # Определяем, откуда пришел запрос
        if update.callback_query:
            await update.callback_query.edit_message_text(game_text, reply_markup=reply_markup)
        else:
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