"""
Интеграция с DeepSeek API для ГМ в Daggerheart
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp
from dataclasses import dataclass

from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, GM_SETTINGS
from game.game_session import GameSession
from game.character import Character

logger = logging.getLogger(__name__)


@dataclass
class GMContext:
    """Контекст для ГМ"""
    session_id: str
    current_scene: str
    active_characters: List[Dict]
    recent_events: List[str]
    story_summary: str
    global_hope: int
    global_fear: int
    player_action: str


class DaggerheartGM:
    """ИИ Гейммастер на базе DeepSeek"""

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.model = GM_SETTINGS.get("model", "deepseek-chat")
        self.temperature = GM_SETTINGS.get("temperature", 0.7)
        self.max_tokens = GM_SETTINGS.get("max_tokens", 1000)

        # Базовый промпт системы
        self.system_prompt = self._build_system_prompt()

        # История взаимодействий для поддержания контекста
        self.conversation_history: Dict[str, List[Dict]] = {}

    def _build_system_prompt(self) -> str:
        """Создать системный промпт для ГМ"""
        return """Ты - опытный Гейммастер в игре Daggerheart, настольной ролевой игре от Critical Role.

ТВОЯ РОЛЬ:
- Создавай увлекательные приключения и интересные ситуации
- Описывай мир живо и детально
- Реагируй на действия игроков осмысленно
- Используй систему Hope/Fear для создания напряжения
- Следуй правилам Daggerheart

ПРАВИЛА DAGGERHEART:
- Игроки бросают 2d12 (Hope и Fear кости)
- Если Hope больше Fear = успех + игрок получает Hope
- Если Fear больше Hope = успех + ГМ получает Fear
- Если кости равны = критический успех
- Персонажи имеют 6 характеристик: Agility, Strength, Finesse, Instinct, Presence, Knowledge
- Хиты работают по порогам урона (1-3 хита за атаку)
- Hope можно тратить на особые способности
- Fear ГМ тратит на осложнения и угрозы

СТИЛЬ ПОВЕСТВОВАНИЯ:
- Отвечай на русском языке
- Используй живые описания и диалоги
- Создавай моральные дилеммы
- Фокусируйся на эмоциях и характере персонажей
- Поощряй творческие решения
- Не бойся добавлять неожиданные повороты

МЕХАНИКИ:
- Когда нужен бросок, просто попроси его: "Брось [характеристику] против сложности [число]"
- Интерпретируй результаты интересно
- Используй Fear для создания осложнений
- Помни про последствия действий

ФОРМАТ ОТВЕТА:
1. Описание того, что происходит
2. Если нужно - запрос броска
3. Опционально - тратa Fear на осложнения
4. Вопрос или выбор для игрока

Всегда помни: цель - создать незабываемую историю вместе с игроками!"""

    async def process_player_action(self, session: GameSession, player_id: str,
                                    action: str) -> Dict[str, Any]:
        """
        Обработать действие игрока и сгенерировать ответ ГМ

        Args:
            session: Игровая сессия
            player_id: ID игрока
            action: Действие игрока

        Returns:
            Dict с ответом ГМ и возможными игровыми эффектами
        """
        try:
            # Собираем контекст
            context = self._build_context(session, player_id, action)

            # Генерируем ответ ГМ
            gm_response = await self._generate_gm_response(context)

            # Обрабатываем игровые эффекты
            effects = self._parse_game_effects(gm_response, session)

            # Сохраняем в историю
            self._update_conversation_history(session.session_id, action, gm_response)

            return {
                "success": True,
                "gm_response": gm_response,
                "effects": effects,
                "context": {
                    "hope": session.global_hope,
                    "fear": session.global_fear,
                    "scene": context.current_scene
                }
            }

        except Exception as e:
            logger.error(f"Ошибка обработки действия: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": self._get_fallback_response()
            }

    def _build_context(self, session: GameSession, player_id: str, action: str) -> GMContext:
        """Построить контекст для ГМ"""
        character = session.characters.get(player_id)
        character_info = {}

        if character:
            character_info = {
                "name": character.name,
                "class": character.character_class.name_ru if character.character_class else "Неизвестно",
                "ancestry": character.ancestry.name_ru if character.ancestry else "Неизвестно",
                "hp": f"{character.current_hp}/{character.hit_points}",
                "traits": {
                    "agility": character.traits.agility,
                    "strength": character.traits.strength,
                    "finesse": character.traits.finesse,
                    "instinct": character.traits.instinct,
                    "presence": character.traits.presence,
                    "knowledge": character.traits.knowledge
                }
            }

        # Информация о всех персонажах в сессии
        all_characters = []
        for pid, char in session.characters.items():
            all_characters.append({
                "name": char.name,
                "class": char.character_class.name_ru if char.character_class else "Неизвестно",
                "hp": f"{char.current_hp}/{char.hit_points}",
                "is_current_player": pid == player_id
            })

        # Текущая сцена
        scene_description = "Исследование"
        if session.current_scene:
            scene_types = {
                "exploration": "Исследование",
                "social": "Социальное взаимодействие",
                "action": "Боевая сцена",
                "rest": "Отдых"
            }
            scene_description = f"{scene_types.get(session.current_scene.type.value, 'Неизвестно')}: {session.current_scene.description}"

        # Недавние события
        recent_events = [event.description for event in session.events[-5:]]

        # Краткая история сессии
        story_summary = " ".join(session.story_log[-3:]) if session.story_log else "Начало приключения"

        return GMContext(
            session_id=session.session_id,
            current_scene=scene_description,
            active_characters=all_characters,
            recent_events=recent_events,
            story_summary=story_summary,
            global_hope=session.global_hope,
            global_fear=session.global_fear,
            player_action=f"{character_info.get('name', 'Игрок')}: {action}"
        )

    async def _generate_gm_response(self, context: GMContext) -> str:
        """Сгенерировать ответ ГМ через DeepSeek API"""

        # Формируем сообщения для API
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._format_context_message(context)}
        ]

        # Добавляем историю разговора если есть
        if context.session_id in self.conversation_history:
            history = self.conversation_history[context.session_id][-6:]  # последние 6 сообщений
            messages.extend(history)

        # Добавляем текущее действие
        messages.append({"role": "user", "content": context.player_action})

        # Отправляем запрос к DeepSeek
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }

            async with session.post(self.api_url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

    def _format_context_message(self, context: GMContext) -> str:
        """Форматировать контекстное сообщение"""
        message = f"""ТЕКУЩАЯ СИТУАЦИЯ:

🎭 Сцена: {context.current_scene}

👥 Персонажи в игре:
{chr(10).join([f"- {char['name']} ({char['class']}) - {char['hp']} хитов" for char in context.active_characters])}

🎲 Пулы:
- Hope: {context.global_hope}
- Fear: {context.global_fear}

📖 Краткая история: {context.story_summary}

🕐 Недавние события:
{chr(10).join([f"• {event}" for event in context.recent_events[-3:]])}

Что происходит дальше?"""

        return message

    def _parse_game_effects(self, gm_response: str, session: GameSession) -> List[Dict]:
        """Извлечь игровые эффекты из ответа ГМ"""
        effects = []

        # Простые паттерны для извлечения эффектов
        import re

        # Поиск запросов бросков
        roll_patterns = [
            r"[Бб]рось\s+(\w+)\s+против\s+сложности\s+(\d+)",
            r"[Сс]делай\s+проверку\s+(\w+)\s+\((\d+)\)",
            r"[Пп]роверка\s+(\w+):\s*(\d+)"
        ]

        for pattern in roll_patterns:
            matches = re.findall(pattern, gm_response, re.IGNORECASE)
            for match in matches:
                trait, difficulty = match
                effects.append({
                    "type": "request_roll",
                    "trait": trait.lower(),
                    "difficulty": int(difficulty),
                    "description": f"Требуется проверка {trait}"
                })

        # Поиск трат Fear
        fear_patterns = [
            r"[Тт]рачу\s+(\d+)\s+Fear",
            r"[Ии]спользую\s+(\d+)\s+Fear"
        ]

        for pattern in fear_patterns:
            matches = re.findall(pattern, gm_response)
            for match in matches:
                amount = int(match)
                if session.global_fear >= amount:
                    effects.append({
                        "type": "spend_fear",
                        "amount": amount,
                        "description": f"ГМ тратит {amount} Fear"
                    })

        # Поиск урона
        damage_patterns = [
            r"получает\s+(\d+)\s+урона",
            r"наносит\s+(\d+)\s+урона"
        ]

        for pattern in damage_patterns:
            matches = re.findall(pattern, gm_response)
            for match in matches:
                damage = int(match)
                effects.append({
                    "type": "damage",
                    "amount": damage,
                    "description": f"Урон: {damage}"
                })

        return effects

    def _update_conversation_history(self, session_id: str, player_action: str, gm_response: str):
        """Обновить историю разговора"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []

        history = self.conversation_history[session_id]
        history.append({"role": "user", "content": player_action})
        history.append({"role": "assistant", "content": gm_response})

        # Ограничиваем историю последними 20 сообщениями
        if len(history) > 20:
            self.conversation_history[session_id] = history[-20:]

    def _get_fallback_response(self) -> str:
        """Запасной ответ при ошибке API"""
        fallback_responses = [
            "Что-то загадочное происходит... (ГМ временно недоступен)",
            "Твое действие разворачивается интересным образом... (Подождите, ГМ думает)",
            "Окружающий мир замирает в ожидании... (Технические трудности)",
            "Судьба задумалась над твоим поступком... (ГМ скоро вернется)"
        ]
        import random
        return random.choice(fallback_responses)

    async def generate_scene_description(self, session: GameSession, scene_type: str,
                                         location: str = "") -> str:
        """Сгенерировать описание новой сцены"""
        try:
            context = f"""Создай описание новой сцены для игры в Daggerheart.

Тип сцены: {scene_type}
Локация: {location or "на усмотрение ГМ"}

Персонажи в группе:
{chr(10).join([f"- {char.name} ({char.character_class.name_ru if char.character_class else 'Неизвестно'})" for char in session.characters.values()])}

Создай атмосферное описание сцены на 2-3 предложения. Включи детали окружения и возможные зацепки для действий."""

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ]

            async with aiohttp.ClientSession() as http_session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 300
                }

                async with http_session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        return f"Вы оказываетесь в новой локации... (ошибка генерации сцены)"

        except Exception as e:
            logger.error(f"Ошибка генерации сцены: {e}")
            return "Перед вами открывается новое место для исследования..."

    def clear_session_history(self, session_id: str):
        """Очистить историю сессии"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]


# Глобальный экземпляр ГМ
daggerheart_gm = DaggerheartGM()


# Функции для интеграции с ботом
async def process_gm_action(session_id: str, player_id: str, action: str) -> Dict:
    """Обработать действие игрока через ГМ"""
    from game.game_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Сессия не найдена"}

    result = await daggerheart_gm.process_player_action(session, player_id, action)

    # Применяем эффекты к сессии
    if result.get("success") and result.get("effects"):
        for effect in result["effects"]:
            await apply_game_effect(session, effect, player_id)

    return result


async def apply_game_effect(session: GameSession, effect: Dict, player_id: str):
    """Применить игровой эффект к сессии"""
    effect_type = effect.get("type")

    if effect_type == "spend_fear":
        amount = effect.get("amount", 1)
        session.spend_fear(amount)

    elif effect_type == "damage":
        amount = effect.get("amount", 1)
        session.deal_damage_to_character(player_id, amount, "игровое событие")

    elif effect_type == "request_roll":
        # Это просто уведомление о необходимости броска
        # Фактический бросок игрок делает сам
        pass


async def start_new_scene(session_id: str, scene_type: str, location: str = "") -> str:
    """Начать новую сцену с описанием от ГМ"""
    from game.game_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return "Ошибка: сессия не найдена"

    description = await daggerheart_gm.generate_scene_description(session, scene_type, location)

    # Обновляем сцену в сессии
    from game.game_session import SceneType
    scene_type_enum = SceneType.EXPLORATION  # по умолчанию
    if scene_type == "action":
        scene_type_enum = SceneType.ACTION
    elif scene_type == "social":
        scene_type_enum = SceneType.SOCIAL
    elif scene_type == "rest":
        scene_type_enum = SceneType.REST

    session.start_scene(scene_type_enum, description, list(session.characters.keys()))

    return description


# Пример использования
if __name__ == "__main__":
    async def test_gm():
        # Тестирование ГМ (требует настроенный API ключ)
        print("Тестирование DeepSeek ГМ...")

        # Здесь будет код для тестирования
        print("Для тестирования нужен настроенный API ключ DeepSeek")

    # asyncio.run(test_gm())