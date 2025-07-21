"""
Система персонажей Daggerheart
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from .mechanics import (
    CharacterTrait, CharacterClass, Ancestry, DaggerheartMechanics,
    get_class_by_id, get_ancestry_by_id, validate_character_traits
)

@dataclass
class Equipment:
    """Снаряжение персонажа"""
    name: str
    name_ru: str
    type: str  # weapon, armor, tool, etc.
    damage: Optional[str] = None  # для оружия (например "2d6+1")
    armor_value: Optional[int] = None  # для брони
    durability: Optional[int] = None  # прочность
    max_durability: Optional[int] = None
    description: str = ""
    special_properties: List[str] = None

    def __post_init__(self):
        if self.special_properties is None:
            self.special_properties = []

@dataclass
class DomainCard:
    """Карта домена (способности/заклинания)"""
    name: str
    name_ru: str
    domain: str  # Blade, Arcana, Wild, etc.
    type: str    # ability or spell
    level: int   # уровень карты
    description: str
    description_ru: str
    mechanics: Dict  # игровые механики
    cost: Optional[str] = None  # стоимость (Hope, Action, etc.)

@dataclass
class CharacterProgress:
    """Прогресс персонажа"""
    level: int = 1
    experience: int = 0
    hope: int = 2  # текущее количество Hope
    max_hope: int = 5  # максимум Hope
    fear_tokens: int = 0  # токены страха на персонаже

class Character:
    """Персонаж игрока в Daggerheart"""

    def __init__(self, name: str, player_id: str):
        self.name = name
        self.player_id = player_id
        self.character_class: Optional[CharacterClass] = None
        self.ancestry: Optional[Ancestry] = None
        self.community: str = ""  # сообщество

        # Характеристики
        self.traits = CharacterTrait()

        # Боевые характеристики
        self.hit_points = 6  # базовые хиты
        self.current_hp = 6
        self.evasion = 10    # уклонение
        self.damage_threshold = 1  # порог урона

        # Прогресс
        self.progress = CharacterProgress()

        # Снаряжение и способности
        self.equipment: List[Equipment] = []
        self.domain_cards: List[DomainCard] = []
        self.inventory: List[str] = []

        # Дополнительная информация
        self.backstory = ""
        self.motivation = ""
        self.connections = []

        # Состояние
        self.is_alive = True
        self.conditions = []  # статус-эффекты

    def set_class(self, class_id: str) -> bool:
        """Установить класс персонажа"""
        character_class = get_class_by_id(class_id)
        if not character_class:
            return False

        self.character_class = character_class
        self._update_class_stats()
        return True

    def set_ancestry(self, ancestry_id: str) -> bool:
        """Установить происхождение персонажа"""
        ancestry = get_ancestry_by_id(ancestry_id)
        if not ancestry:
            return False

        self.ancestry = ancestry
        self._apply_ancestry_bonuses()
        return True

    def set_traits(self, agility: int, strength: int, finesse: int,
                   instinct: int, presence: int, knowledge: int) -> bool:
        """Установить характеристики персонажа"""
        new_traits = CharacterTrait(
            agility=agility, strength=strength, finesse=finesse,
            instinct=instinct, presence=presence, knowledge=knowledge
        )

        if not validate_character_traits(new_traits):
            return False

        self.traits = new_traits
        return True

    def _update_class_stats(self):
        """Обновить характеристики на основе класса"""
        if not self.character_class:
            return

        self.hit_points = self.character_class.hit_points_base
        self.current_hp = self.hit_points
        self.evasion = self.character_class.evasion_base
        self.damage_threshold = self.character_class.damage_threshold

    def _apply_ancestry_bonuses(self):
        """Применить бонусы происхождения"""
        if not self.ancestry:
            return

        for trait_name, bonus in self.ancestry.trait_bonuses.items():
            current_value = self.traits.get_trait_value(trait_name)
            new_value = min(3, max(-3, current_value + bonus))  # ограничение -3 до +3
            setattr(self.traits, trait_name, new_value)

    def add_equipment(self, equipment: Equipment):
        """Добавить снаряжение"""
        self.equipment.append(equipment)

    def add_domain_card(self, card: DomainCard):
        """Добавить карту домена"""
        self.domain_cards.append(card)

    def gain_hope(self, amount: int = 1):
        """Получить Hope"""
        self.progress.hope = min(self.progress.max_hope, self.progress.hope + amount)

    def spend_hope(self, amount: int = 1) -> bool:
        """Потратить Hope"""
        if self.progress.hope >= amount:
            self.progress.hope -= amount
            return True
        return False

    def take_damage(self, damage: int) -> Dict:
        """Получить урон"""
        new_hp, actual_damage = DaggerheartMechanics.apply_damage(
            self.current_hp, damage, self.damage_threshold
        )

        old_hp = self.current_hp
        self.current_hp = new_hp

        result = {
            "old_hp": old_hp,
            "new_hp": new_hp,
            "damage_dealt": actual_damage,
            "damage_blocked": damage - actual_damage if actual_damage < damage else 0,
            "is_unconscious": new_hp == 0,
            "is_dying": new_hp == 0 and old_hp > 0
        }

        if new_hp == 0:
            self._handle_dying()

        return result

    def heal(self, amount: int):
        """Восстановить здоровье"""
        self.current_hp = min(self.hit_points, self.current_hp + amount)

    def _handle_dying(self):
        """Обработка состояния при 0 хитов"""
        # В Daggerheart есть три варианта:
        # 1. Blaze of Glory (смерть с критическим успехом)
        # 2. Avoid Death (потеря 1 max Hope)
        # 3. Risk It All (бросок Hope/Fear)
        pass

    def make_action_roll(self, trait_name: str, difficulty: int = 12,
                        advantage: bool = False, disadvantage: bool = False):
        """Совершить проверку действия"""
        trait_value = self.traits.get_trait_value(trait_name)
        dice_roll, success = DaggerheartMechanics.make_trait_roll(
            trait_value, difficulty, advantage, disadvantage
        )

        # Обработка результата
        if dice_roll.result_type.value == "success_with_hope":
            self.gain_hope(1)

        return {
            "dice_roll": dice_roll,
            "success": success,
            "trait_used": trait_name,
            "trait_value": trait_value,
            "difficulty": difficulty,
            "total": dice_roll.total + trait_value,
            "formatted_result": DaggerheartMechanics.format_dice_result(
                dice_roll, trait_value, difficulty, success
            )
        }

    def get_character_sheet(self) -> Dict:
        """Получить лист персонажа в виде словаря"""
        return {
            "basic_info": {
                "name": self.name,
                "class": self.character_class.name_ru if self.character_class else "Не выбран",
                "ancestry": self.ancestry.name_ru if self.ancestry else "Не выбрано",
                "community": self.community,
                "level": self.progress.level
            },
            "traits": asdict(self.traits),
            "combat_stats": {
                "hit_points": f"{self.current_hp}/{self.hit_points}",
                "evasion": self.evasion,
                "damage_threshold": self.damage_threshold
            },
            "progress": {
                "hope": f"{self.progress.hope}/{self.progress.max_hope}",
                "experience": self.progress.experience,
                "fear_tokens": self.progress.fear_tokens
            },
            "equipment": [eq.name_ru for eq in self.equipment],
            "domain_cards": [card.name_ru for card in self.domain_cards],
            "status": {
                "alive": self.is_alive,
                "conditions": self.conditions
            }
        }

    def to_json(self) -> str:
        """Сериализация персонажа в JSON"""
        data = {
            "name": self.name,
            "player_id": self.player_id,
            "class_id": self.character_class.name.lower() if self.character_class else None,
            "ancestry_id": self.ancestry.name.lower() if self.ancestry else None,
            "community": self.community,
            "traits": asdict(self.traits),
            "hit_points": self.hit_points,
            "current_hp": self.current_hp,
            "evasion": self.evasion,
            "damage_threshold": self.damage_threshold,
            "progress": asdict(self.progress),
            "equipment": [asdict(eq) for eq in self.equipment],
            "domain_cards": [asdict(card) for card in self.domain_cards],
            "inventory": self.inventory,
            "backstory": self.backstory,
            "motivation": self.motivation,
            "connections": self.connections,
            "is_alive": self.is_alive,
            "conditions": self.conditions
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_data: str):
        """Десериализация персонажа из JSON"""
        data = json.loads(json_data)

        character = cls(data["name"], data["player_id"])

        # Восстановление класса и происхождения
        if data["class_id"]:
            character.set_class(data["class_id"])
        if data["ancestry_id"]:
            character.set_ancestry(data["ancestry_id"])

        character.community = data["community"]

        # Восстановление характеристик
        traits_data = data["traits"]
        character.traits = CharacterTrait(**traits_data)

        # Восстановление боевых характеристик
        character.hit_points = data["hit_points"]
        character.current_hp = data["current_hp"]
        character.evasion = data["evasion"]
        character.damage_threshold = data["damage_threshold"]

        # Восстановление прогресса
        progress_data = data["progress"]
        character.progress = CharacterProgress(**progress_data)

        # Восстановление снаряжения
        for eq_data in data["equipment"]:
            equipment = Equipment(**eq_data)
            character.equipment.append(equipment)

        # Восстановление карт доменов
        for card_data in data["domain_cards"]:
            card = DomainCard(**card_data)
            character.domain_cards.append(card)

        # Остальные поля
        character.inventory = data["inventory"]
        character.backstory = data["backstory"]
        character.motivation = data["motivation"]
        character.connections = data["connections"]
        character.is_alive = data["is_alive"]
        character.conditions = data["conditions"]

        return character

# Предустановленное снаряжение
STARTING_EQUIPMENT = {
    "guardian": [
        Equipment("Shield", "Щит", "armor", armor_value=2, durability=5, max_durability=5),
        Equipment("Sword", "Меч", "weapon", damage="2d6+1", description="Надежное оружие стража")
    ],
    "ranger": [
        Equipment("Bow", "Лук", "weapon", damage="2d6", description="Дальнобойное оружие"),
        Equipment("Quiver", "Колчан", "tool", description="30 стрел")
    ],
    "rogue": [
        Equipment("Dagger", "Кинжал", "weapon", damage="1d6+2", description="Быстрое и точное оружие"),
        Equipment("Thieves' Tools", "Воровские инструменты", "tool", description="Для взлома замков")
    ],
    "seraph": [
        Equipment("Holy Symbol", "Святой символ", "tool", description="Фокус для божественной магии"),
        Equipment("Healing Kit", "Аптечка", "tool", description="Базовое лечение")
    ],
    "sorcerer": [
        Equipment("Spellbook", "Книга заклинаний", "tool", description="Содержит изученные заклинания"),
        Equipment("Focus Crystal", "Кристалл фокусировки", "tool", description="Усиливает магию")
    ],
    "warrior": [
        Equipment("Battle Axe", "Боевой топор", "weapon", damage="2d6+2", description="Мощное двуручное оружие"),
        Equipment("Leather Armor", "Кожаная броня", "armor", armor_value=1, durability=3, max_durability=3)
    ]
}

# Базовые карты доменов
BASIC_DOMAIN_CARDS = {
    "blade": [
        DomainCard(
            "Strike", "Удар", "Blade", "ability", 1,
            "A basic melee attack", "Базовая атака ближнего боя",
            {"action_type": "attack", "range": "melee", "damage": "weapon"}
        ),
        DomainCard(
            "Parry", "Парирование", "Blade", "ability", 1,
            "Deflect an incoming attack", "Отразить входящую атаку",
            {"action_type": "reaction", "effect": "reduce_damage"}
        )
    ],
    "arcana": [
        DomainCard(
            "Magic Missile", "Магическая стрела", "Arcana", "spell", 1,
            "Unerring magical projectile", "Безошибочный магический снаряд",
            {"action_type": "attack", "range": "far", "damage": "1d6+knowledge", "auto_hit": True}
        ),
        DomainCard(
            "Detect Magic", "Обнаружение магии", "Arcana", "spell", 1,
            "Sense magical auras", "Почувствовать магические ауры",
            {"action_type": "utility", "range": "close", "duration": "scene"}
        )
    ],
    "grace": [
        DomainCard(
            "Healing Word", "Слово исцеления", "Grace", "spell", 1,
            "Restore hit points with divine magic", "Восстановить хиты божественной магией",
            {"action_type": "utility", "range": "close", "healing": "1d6+presence"}
        ),
        DomainCard(
            "Bless", "Благословение", "Grace", "spell", 1,
            "Grant divine favor", "Даровать божественную милость",
            {"action_type": "utility", "range": "close", "effect": "advantage_next_roll"}
        )
    ]
}

def create_starting_character(name: str, player_id: str, class_id: str,
                            ancestry_id: str, trait_distribution: Dict[str, int]) -> Character:
    """
    Создать стартового персонажа с базовым снаряжением

    Args:
        name: Имя персонажа
        player_id: ID игрока
        class_id: ID класса
        ancestry_id: ID происхождения
        trait_distribution: Распределение характеристик
    """
    character = Character(name, player_id)

    # Установить класс и происхождение
    if not character.set_class(class_id):
        raise ValueError(f"Неизвестный класс: {class_id}")

    if not character.set_ancestry(ancestry_id):
        raise ValueError(f"Неизвестное происхождение: {ancestry_id}")

    # Установить характеристики
    if not character.set_traits(**trait_distribution):
        raise ValueError("Неправильное распределение характеристик")

    # Добавить стартовое снаряжение
    starting_equipment = STARTING_EQUIPMENT.get(class_id, [])
    for equipment in starting_equipment:
        character.add_equipment(equipment)

    # Добавить базовые карты доменов
    class_obj = get_class_by_id(class_id)
    if class_obj and class_obj.domains:
        # Даем по одной карте из каждого домена класса
        for domain in class_obj.domains[:2]:  # максимум 2 карты на старте
            domain_cards = BASIC_DOMAIN_CARDS.get(domain.lower(), [])
            if domain_cards:
                character.add_domain_card(domain_cards[0])  # первая карта домена

    return character

def get_character_creation_guide() -> Dict:
    """Получить руководство по созданию персонажа"""
    return {
        "steps": [
            "1. Выберите класс персонажа",
            "2. Выберите происхождение",
            "3. Распределите 4 очка характеристик",
            "4. Уменьшите любую характеристику на 1",
            "5. Получите стартовое снаряжение",
            "6. Выберите карты доменов"
        ],
        "classes": {k: v.name_ru for k, v in CLASSES.items()},
        "ancestries": {k: v.name_ru for k, v in ANCESTRIES.items()},
        "traits": {
            "agility": "Ловкость (уклонение, акробатика)",
            "strength": "Сила (урон, поднятие тяжестей)",
            "finesse": "Точность (стрельба, тонкая работа)",
            "instinct": "Интуиция (восприятие, выживание)",
            "presence": "Присутствие (лидерство, убеждение)",
            "knowledge": "Знания (магия, исследования)"
        },
        "rules": [
            "Каждая характеристика от -3 до +3",
            "Сумма всех характеристик должна быть 3",
            "Сначала распределите 4 очка, потом вычтите 1"
        ]
    }

# Пример использования
if __name__ == "__main__":
    # Создание тестового персонажа
    traits = {
        "agility": 1,
        "strength": 2,
        "finesse": 0,
        "instinct": 1,
        "presence": 0,
        "knowledge": -1
    }

    character = create_starting_character(
        "Торин Железнобород", "player123", "guardian", "dwarf", traits
    )

    print("Персонаж создан!")
    print(json.dumps(character.get_character_sheet(), ensure_ascii=False, indent=2))

    # Тест броска
    result = character.make_action_roll("strength", difficulty=12)
    print(f"\nТест броска силы:")
    print(result["formatted_result"])