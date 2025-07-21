"""
Система игровых сессий Daggerheart
"""

import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum

from .character import Character
from .mechanics import DaggerheartMechanics, ActionResult


class SessionState(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class SceneType(Enum):
    EXPLORATION = "exploration"
    SOCIAL = "social"
    ACTION = "action"
    REST = "rest"


@dataclass
class GameEvent:
    """Событие в игре"""
    id: str
    timestamp: datetime
    event_type: str  # dice_roll, damage, healing, story, etc.
    character_id: Optional[str]
    description: str
    details: Dict[str, Any]


@dataclass
class SceneState:
    """Состояние текущей сцены"""
    type: SceneType
    description: str
    active_characters: List[str]  # ID персонажей в сцене
    round_number: int = 0
    current_turn: Optional[str] = None  # ID текущего персонажа
    scene_hope: int = 0  # Hope пулл сцены
    scene_fear: int = 0  # Fear пулл сцены


class GameSession:
    """Игровая сессия Daggerheart"""

    def __init__(self, session_id: str, gm_id: str, session_name: str = ""):
        self.session_id = session_id
        self.gm_id = gm_id
        self.session_name = session_name or f"Сессия {session_id[:8]}"

        # Состояние сессии
        self.state = SessionState.WAITING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Участники
        self.characters: Dict[str, Character] = {}  # player_id -> Character
        self.max_players = 6

        # Текущее состояние игры
        self.current_scene: Optional[SceneState] = None
        self.global_hope = 0
        self.global_fear = 0

        # История событий
        self.events: List[GameEvent] = []
        self.story_log: List[str] = []

        # Настройки сессии
        self.settings = {
            "auto_save": True,
            "public_rolls": True,
            "allow_spectators": False,
            "session_timeout": 3600  # 1 час бездействия
        }

    def add_player(self, player_id: str, character: Character) -> bool:
        """Добавить игрока в сессию"""
        if len(self.characters) >= self.max_players:
            return False

        if player_id in self.characters:
            return False

        self.characters[player_id] = character
        self._log_event("player_joined", None, f"{character.name} присоединился к игре")
        return True

    def remove_player(self, player_id: str) -> bool:
        """Удалить игрока из сессии"""
        if player_id not in self.characters:
            return False

        character_name = self.characters[player_id].name
        del self.characters[player_id]
        self._log_event("player_left", None, f"{character_name} покинул игру")
        return True

    def start_session(self) -> bool:
        """Начать игровую сессию"""
        if self.state != SessionState.WAITING:
            return False

        if len(self.characters) == 0:
            return False

        self.state = SessionState.ACTIVE
        self.started_at = datetime.now()

        # Начинаем с исследовательской сцены
        self.start_scene(SceneType.EXPLORATION, "Начало приключения", list(self.characters.keys()))

        self._log_event("session_started", None, "Игровая сессия началась!")
        return True

    def start_scene(self, scene_type: SceneType, description: str, character_ids: List[str]):
        """Начать новую сцену"""
        self.current_scene = SceneState(
            type=scene_type,
            description=description,
            active_characters=character_ids,
            round_number=1 if scene_type == SceneType.ACTION else 0
        )

        # В боевой сцене определяем порядок ходов
        if scene_type == SceneType.ACTION and character_ids:
            self.current_scene.current_turn = character_ids[0]

        self._log_event("scene_started", None, f"Начата сцена: {description}")

    def end_scene(self):
        """Завершить текущую сцену"""
        if self.current_scene:
            scene_desc = self.current_scene.description
            self.current_scene = None
            self._log_event("scene_ended", None, f"Завершена сцена: {scene_desc}")

    def next_turn(self):
        """Следующий ход в боевой сцене"""
        if not self.current_scene or self.current_scene.type != SceneType.ACTION:
            return

        active_chars = self.current_scene.active_characters
        if not active_chars:
            return

        current_index = 0
        if self.current_scene.current_turn:
            try:
                current_index = active_chars.index(self.current_scene.current_turn)
            except ValueError:
                pass

        # Следующий персонаж или новый раунд
        next_index = (current_index + 1) % len(active_chars)
        if next_index == 0:
            self.current_scene.round_number += 1

        self.current_scene.current_turn = active_chars[next_index]

        character_name = self.characters[active_chars[next_index]].name
        self._log_event("turn_started", active_chars[next_index], f"Ход {character_name}")

    def make_character_roll(self, player_id: str, trait_name: str, difficulty: int = 12,
                            advantage: bool = False, disadvantage: bool = False) -> Dict:
        """Персонаж совершает бросок"""
        if player_id not in self.characters:
            return {"error": "Персонаж не найден"}

        character = self.characters[player_id]
        result = character.make_action_roll(trait_name, difficulty, advantage, disadvantage)

        # Обновляем пулы Hope/Fear
        if result["dice_roll"].result_type == ActionResult.SUCCESS_WITH_HOPE:
            self.global_hope += 1
        elif result["dice_roll"].result_type == ActionResult.SUCCESS_WITH_FEAR:
            self.global_fear += 1

        # Логируем событие
        self._log_event(
            "dice_roll",
            player_id,
            f"{character.name} бросает {trait_name}: {result['formatted_result']}",
            result
        )

        return result

    def deal_damage_to_character(self, player_id: str, damage: int, source: str = "") -> Dict:
        """Нанести урон персонажу"""
        if player_id not in self.characters:
            return {"error": "Персонаж не найден"}

        character = self.characters[player_id]
        damage_result = character.take_damage(damage)

        description = f"{character.name} получает {damage_result['damage_dealt']} урона"
        if damage_result['damage_blocked'] > 0:
            description += f" ({damage_result['damage_blocked']} заблокировано)"

        if source:
            description += f" от {source}"

        self._log_event("damage_dealt", player_id, description, damage_result)

        if damage_result['is_dying']:
            self._log_event("character_dying", player_id, f"{character.name} при смерти!")

        return damage_result

    def heal_character(self, player_id: str, amount: int, source: str = "") -> Dict:
        """Исцелить персонажа"""
        if player_id not in self.characters:
            return {"error": "Персонаж не найден"}

        character = self.characters[player_id]
        old_hp = character.current_hp
        character.heal(amount)
        actual_healing = character.current_hp - old_hp

        description = f"{character.name} восстанавливает {actual_healing} хитов"
        if source:
            description += f" от {source}"

        result = {
            "old_hp": old_hp,
            "new_hp": character.current_hp,
            "healing": actual_healing
        }

        self._log_event("healing", player_id, description, result)
        return result

    def add_story_event(self, description: str, character_id: Optional[str] = None):
        """Добавить сюжетное событие"""
        self.story_log.append(description)
        self._log_event("story", character_id, description)

    def spend_hope(self, amount: int) -> bool:
        """Потратить Hope из глобального пула"""
        if self.global_hope >= amount:
            self.global_hope -= amount
            self._log_event("hope_spent", None, f"Потрачено {amount} Hope")
            return True
        return False

    def spend_fear(self, amount: int) -> bool:
        """Потратить Fear из пула ГМ"""
        if self.global_fear >= amount:
            self.global_fear -= amount
            self._log_event("fear_spent", None, f"ГМ тратит {amount} Fear")
            return True
        return False

    def get_session_status(self) -> Dict:
        """Получить статус сессии"""
        active_characters = []
        for player_id, character in self.characters.items():
            char_info = {
                "player_id": player_id,
                "name": character.name,
                "class": character.character_class.name_ru if character.character_class else "Неизвестно",
                "hp": f"{character.current_hp}/{character.hit_points}",
                "hope": f"{character.progress.hope}/{character.progress.max_hope}",
                "is_alive": character.is_alive,
                "is_current_turn": (self.current_scene and
                                    self.current_scene.current_turn == player_id)
            }
            active_characters.append(char_info)

        current_scene_info = None
        if self.current_scene:
            current_scene_info = {
                "type": self.current_scene.type.value,
                "description": self.current_scene.description,
                "round": self.current_scene.round_number,
                "current_turn": self.current_scene.current_turn
            }

        return {
            "session_id": self.session_id,
            "name": self.session_name,
            "state": self.state.value,
            "gm_id": self.gm_id,
            "players_count": len(self.characters),
            "max_players": self.max_players,
            "global_hope": self.global_hope,
            "global_fear": self.global_fear,
            "current_scene": current_scene_info,
            "characters": active_characters,
            "uptime": str(datetime.now() - self.created_at) if self.created_at else "0:00:00"
        }

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """Получить недавние события"""
        recent_events = self.events[-limit:] if self.events else []
        return [
            {
                "id": event.id,
                "timestamp": event.timestamp.strftime("%H:%M:%S"),
                "type": event.event_type,
                "character_id": event.character_id,
                "description": event.description
            }
            for event in recent_events
        ]

    def _log_event(self, event_type: str, character_id: Optional[str],
                   description: str, details: Dict = None):
        """Записать событие в лог"""
        event = GameEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            character_id=character_id,
            description=description,
            details=details or {}
        )
        self.events.append(event)

        # Автосохранение если включено
        if self.settings.get("auto_save", True):
            self._auto_save()

    def _auto_save(self):
        """Автоматическое сохранение (заглушка)"""
        # Здесь будет логика сохранения в базу данных
        pass

    def to_json(self) -> str:
        """Сериализация сессии в JSON"""
        data = {
            "session_id": self.session_id,
            "gm_id": self.gm_id,
            "session_name": self.session_name,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "characters": {pid: char.to_json() for pid, char in self.characters.items()},
            "current_scene": asdict(self.current_scene) if self.current_scene else None,
            "global_hope": self.global_hope,
            "global_fear": self.global_fear,
            "story_log": self.story_log,
            "settings": self.settings
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class SessionManager:
    """Менеджер игровых сессий"""

    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}

    def create_session(self, gm_id: str, session_name: str = "") -> str:
        """Создать новую сессию"""
        session_id = str(uuid.uuid4())
        session = GameSession(session_id, gm_id, session_name)
        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[GameSession]:
        """Получить сессию по ID"""
        return self.sessions.get(session_id)

    def join_session(self, session_id: str, player_id: str, character: Character) -> bool:
        """Присоединиться к сессии"""
        session = self.get_session(session_id)
        if not session:
            return False
        return session.add_player(player_id, character)

    def list_active_sessions(self) -> List[Dict]:
        """Список активных сессий"""
        active_sessions = []
        for session in self.sessions.values():
            if session.state in [SessionState.WAITING, SessionState.ACTIVE]:
                active_sessions.append(session.get_session_status())
        return active_sessions

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Очистка старых сессий"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        to_remove = []
        for session_id, session in self.sessions.items():
            if (session.state == SessionState.COMPLETED or
                    (session.created_at and session.created_at < cutoff_time)):
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.sessions[session_id]

        return len(to_remove)


# Глобальный менеджер сессий
session_manager = SessionManager()

# Пример использования
if __name__ == "__main__":
    from .character import create_starting_character

    # Создание тестовой сессии
    session_id = session_manager.create_session("gm123", "Тестовая игра")
    session = session_manager.get_session(session_id)

    # Создание персонажа
    traits = {"agility": 1, "strength": 2, "finesse": 0, "instinct": 1, "presence": 0, "knowledge": -1}
    character = create_starting_character("Эльдан", "player1", "guardian", "elf", traits)

    # Добавление игрока
    session.add_player("player1", character)

    # Начало сессии
    session.start_session()

    # Тестовый бросок
    result = session.make_character_roll("player1", "strength", 12)
    print(f"Результат броска: {result['success']}")

    # Статус сессии
    status = session.get_session_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))