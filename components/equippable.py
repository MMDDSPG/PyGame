from typing import Optional, TYPE_CHECKING

import actions
from components.base_component import BaseComponent
from equipment_types import EquipmentType
from input_handlers import ActionOrHandler

if TYPE_CHECKING:
    from entity import Actor, Item


class Equippable(BaseComponent):
    parent: "Item"

    # 初始化装备
    # equipment_type: 装备类型
    # power_bonus: 力量加成
    # defense_bonus: 防御加成
    def __init__(
        self,
        equipment_type: EquipmentType,
        power_bonus: int = 0,
        defense_bonus: int = 0,
    ):
        self.equipment_type = equipment_type

        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus

    def get_action(self, consumer: "Actor") -> Optional[ActionOrHandler]:
        return actions.EquipAction(consumer, self.parent)


# 匕首
class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)


# 剑
class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)


# 皮甲
class LeatherArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)


# 锁子甲
class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)