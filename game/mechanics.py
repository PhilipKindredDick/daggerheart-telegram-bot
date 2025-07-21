"""
Игровые механики Daggerheart
Основано на официальных правилах системы
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class DiceType(Enum):
    HOPE = "hope"
    FEAR = "fear"


class ActionResult(Enum):
    CRITICAL_SUCCESS = "critical_success"
    SUCCESS_WITH_HOPE = "success_with_hope"
    SUCCESS_WITH_FEAR = "success_with_fear"
    FAILURE = "failure"


@dataclass
class DiceRoll:
    """Результат броска костей Hope/Fear"""
    hope_die: int
    fear_die: int
    bonus: int = 0
    total: int = 0
    result_type: ActionResult = ActionResult.FAILURE

    def __post_init__(self):
        self.total = self.hope_die + self.fear_die + self.bonus
        self._determine_result()

    def _determine_result(self):
        if self.hope_die == self.fear_die:
            self.result_type = ActionResult.CRITICAL_SUCCESS
        elif self.hope_die > self.fear_die:
            self.result_type = ActionResult.SUCCESS_WITH_HOPE
        elif self.fear_die > self.hope_die:
            self.result_type = ActionResult.SUCCESS_WITH_FEAR
        else:
            self.result_type = ActionResult.FAILURE


@dataclass
class CharacterTrait:
    """Характеристики персонажа"""
    agility: int = 0  # Ловкость
    strength: int = 0  # Сила
    finesse: int = 0  # Точность
    instinct: int = 0  # Интуиция
    presence: int = 0  # Присутствие
    knowledge: int = 0  # Знания

    def get_trait_value(self, trait_name: str) -> int:
        return getattr(self, trait_name.lower(), 0)


@dataclass
class CharacterClass:
    """Класс персонажа"""
    name: str
    name_ru: str
    description: str
    description_ru: str
    evasion_base: int
    hit_points_base: int
    damage_threshold: int
    domains: List[str]
    starting_equipment: List[str]
    special_abilities: List[str]


# Определение классов персонажей
CLASSES = {
    "guardian": CharacterClass(
        name="Guardian",
        name_ru="Страж",
        description="You run into danger to protect your party",
        description_ru="Вы бросаетесь в опасность, чтобы защитить свою команду",
        evasion_base=12,
        hit_points_base=6,
        damage_threshold=3,
        domains=["Valor", "Blade"],
        starting_equipment=["Shield", "Sword"],
        special_abilities=["Armor Mastery", "Guardian's Resolve"]
    ),
    "ranger": CharacterClass(
        name="Ranger",
        name_ru="Следопыт",
        description="Your keen eyes and graceful haste make you indispensable",
        description_ru="Ваши острые глаза и грациозная поспешность делают вас незаменимым",
        evasion_base=14,
        hit_points_base=5,
        damage_threshold=2,
        domains=["Bow", "Wild"],
        starting_equipment=["Bow", "Quiver"],
        special_abilities=["Hunter's Mark", "Wild Sense"]
    ),
    "rogue": CharacterClass(
        name="Rogue",
        name_ru="Плут",
        description="You fight with your blade as well as your wit",
        description_ru="Вы сражаетесь клинком так же, как и остроумием",
        evasion_base=15,
        hit_points_base=4,
        damage_threshold=2,
        domains=["Blade", "Midnight"],
        starting_equipment=["Dagger", "Thieves' Tools"],
        special_abilities=["Sneak Attack", "Quick Reflexes"]
    ),
    "seraph": CharacterClass(
        name="Seraph",
        name_ru="Серафим",
        description="You've taken a vow to a god who helps you channel sacred power",
        description_ru="Вы дали обет богу, который помогает вам направлять священную силу",
        evasion_base=11,
        hit_points_base=5,
        damage_threshold=2,
        domains=["Grace", "Splendor"],
        starting_equipment=["Holy Symbol", "Healing Kit"],
        special_abilities=["Divine Magic", "Healing Touch"]
    ),
    "sorcerer": CharacterClass(
        name="Sorcerer",
        name_ru="Чародей",
        description="You were born with innate magical power",
        description_ru="Вы родились с врожденной магической силой",
        evasion_base=10,
        hit_points_base=4,
        damage_threshold=1,
        domains=["Arcana", "Elemental"],
        starting_equipment=["Spellbook", "Focus Crystal"],
        special_abilities=["Volatile Magic", "Arcane Sense"]
    ),
    "warrior": CharacterClass(
        name="Warrior",
        name_ru="Воин",
        description="You run into battle without hesitation",
        description_ru="Вы бросаетесь в бой без колебаний",
        evasion_base=13,
        hit_points_base=6,
        damage_threshold=3,
        domains=["Blade", "Bone"],
        starting_equipment=["Weapon", "Armor"],
        special_abilities=["Battle Fury", "Weapon Mastery"]
    )
}


@dataclass
class Ancestry:
    """Происхождение персонажа"""
    name: str
    name_ru: str
    description: str
    description_ru: str
    trait_bonuses: Dict[str, int]
    special_features: List[str]


# Происхождения
ANCESTRIES = {
    "human": Ancestry(
        name="Human",
        name_ru="Человек",
        description="Versatile and ambitious",
        description_ru="Универсальные и амбициозные",
        trait_bonuses={"presence": 1},
        special_features=["Versatility", "Determination"]
    ),
    "elf": Ancestry(
        name="Elf",
        name_ru="Эльф",
        description="Graceful and magical",
        description_ru="Грациозные и магические",
        trait_bonuses={"finesse": 1, "knowledge": 1},
        special_features=["Keen Senses", "Magic Affinity"]
    ),
    "dwarf": Ancestry(
        name="Dwarf",
        name_ru="Дворф",
        description="Hardy and resilient",
        description_ru="Выносливые и стойкие",
        trait_bonuses={"strength": 1, "instinct": 1},
        special_features=["Stone Sense", "Crafting Expertise"]
    ),
    "orc": Ancestry(
        name="Orc",
        name_ru="Орк",
        description="Strong and fierce",
        description_ru="Сильные и свирепые",
        trait_bonuses={"strength": 2},
        special_features=["Fierce", "Intimidating Presence"]
    )
}


class DaggerheartMechanics:
    """Основные игровые механики Daggerheart"""

    @staticmethod
    def roll_duality_dice(advantage: bool = False, disadvantage: bool = False) -> DiceRoll:
        """
        Бросок дуальных костей Hope/Fear (2d12)

        Args:
            advantage: Бонус d6 к результату
            disadvantage: Штраф d6 от результата
        """
        hope_die = random.randint(1, 12)
        fear_die = random.randint(1, 12)

        bonus = 0
        if advantage:
            bonus = random.randint(1, 6)
        elif disadvantage:
            bonus = -random.randint(1, 6)

        return DiceRoll(hope_die=hope_die, fear_die=fear_die, bonus=bonus)

    @staticmethod
    def make_trait_roll(trait_value: int, difficulty: int = 12,
                        advantage: bool = False, disadvantage: bool = False) -> Tuple[DiceRoll, bool]:
        """
        Проверка характеристики

        Args:
            trait_value: Значение характеристики (-3 до +3)
            difficulty: Сложность проверки (обычно 12)
            advantage/disadvantage: Модификаторы броска

        Returns:
            Tuple[DiceRoll, bool]: результат броска и успех/неудача
        """
        dice_roll = DaggerheartMechanics.roll_duality_dice(advantage, disadvantage)
        total_with_trait = dice_roll.total + trait_value
        success = total_with_trait >= difficulty

        return dice_roll, success

    @staticmethod
    def calculate_damage(weapon_damage: str, success_level: ActionResult) -> int:
        """
        Расчет урона на основе успеха

        Args:
            weapon_damage: Строка урона оружия (например "2d6+1")
            success_level: Уровень успеха броска
        """
        # Базовый урон (упрощенная реализация)
        base_damage = random.randint(1, 6) + random.randint(1, 6)  # 2d6

        if success_level == ActionResult.CRITICAL_SUCCESS:
            return base_damage * 2  # Критический урон
        elif success_level == ActionResult.SUCCESS_WITH_HOPE:
            return base_damage + 2  # Бонус за Hope
        elif success_level == ActionResult.SUCCESS_WITH_FEAR:
            return base_damage  # Обычный урон
        else:
            return 0  # Промах

    @staticmethod
    def apply_damage(character_hp: int, damage: int, damage_threshold: int) -> Tuple[int, int]:
        """
        Применение урона к персонажу

        Args:
            character_hp: Текущие хиты персонажа
            damage: Входящий урон
            damage_threshold: Порог урона персонажа

        Returns:
            Tuple[int, int]: новые хиты, фактический урон
        """
        if damage >= damage_threshold * 3:
            actual_damage = 3  # Максимальный урон за атаку
        elif damage >= damage_threshold * 2:
            actual_damage = 2
        elif damage >= damage_threshold:
            actual_damage = 1
        else:
            actual_damage = 0  # Урон поглощен

        new_hp = max(0, character_hp - actual_damage)
        return new_hp, actual_damage

    @staticmethod
    def format_dice_result(dice_roll: DiceRoll, trait_value: int = 0,
                           difficulty: int = 12, success: bool = False) -> str:
        """Форматирование результата броска для отображения"""

        result_emoji = {
            ActionResult.CRITICAL_SUCCESS: "🎯",
            ActionResult.SUCCESS_WITH_HOPE: "✨",
            ActionResult.SUCCESS_WITH_FEAR: "⚡",
            ActionResult.FAILURE: "💥"
        }

        emoji = result_emoji.get(dice_roll.result_type, "🎲")

        total_with_trait = dice_roll.total + trait_value
        success_text = "Успех!" if success else "Неудача"

        result = f"{emoji} **{success_text}**\n"
        result += f"🎲 Hope: {dice_roll.hope_die} | Fear: {dice_roll.fear_die}\n"

        if dice_roll.bonus != 0:
            bonus_text = f"+{dice_roll.bonus}" if dice_roll.bonus > 0 else str(dice_roll.bonus)
            result += f"🎯 Модификатор: {bonus_text}\n"

        if trait_value != 0:
            trait_text = f"+{trait_value}" if trait_value > 0 else str(trait_value)
            result += f"💪 Характеристика: {trait_text}\n"

        result += f"📊 Итого: {total_with_trait} (нужно {difficulty})\n"

        # Добавляем объяснение результата
        if dice_roll.result_type == ActionResult.CRITICAL_SUCCESS:
            result += "🌟 Критический успех! Что-то удивительное происходит!"
        elif dice_roll.result_type == ActionResult.SUCCESS_WITH_HOPE:
            result += "✨ Успех с Надеждой! Получаете +1 Hope"
        elif dice_roll.result_type == ActionResult.SUCCESS_WITH_FEAR:
            result += "⚡ Успех со Страхом! ГМ получает +1 Fear"

        return result


def get_class_by_id(class_id: str) -> Optional[CharacterClass]:
    """Получить класс персонажа по ID"""
    return CLASSES.get(class_id.lower())


def get_ancestry_by_id(ancestry_id: str) -> Optional[Ancestry]:
    """Получить происхождение по ID"""
    return ANCESTRIES.get(ancestry_id.lower())


def validate_character_traits(traits: CharacterTrait) -> bool:
    """Проверка правильности распределения характеристик"""
    total = (traits.agility + traits.strength + traits.finesse +
             traits.instinct + traits.presence + traits.knowledge)

    # В Daggerheart сумма характеристик должна быть 3
    # (4 очка распределяем, потом -1 от любой характеристики)
    return total == 3


# Пример использования
if __name__ == "__main__":
    # Тестовый бросок
    dice = DaggerheartMechanics.roll_duality_dice()
    print(f"Hope: {dice.hope_die}, Fear: {dice.fear_die}, Total: {dice.total}")
    print(f"Result: {dice.result_type}")

    # Проверка характеристики
    roll, success = DaggerheartMechanics.make_trait_roll(trait_value=2, difficulty=12)
    print(f"Trait roll: {success}, {roll.result_type}")