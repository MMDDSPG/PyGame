from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):
    parent: "Actor"

    # 初始化装备栏
    def __init__(self, weapon: Optional["Item"] = None, armor: Optional["Item"] = None):
        self.weapon = weapon
        self.armor = armor

    # 计算防御力
    @property
    def defense_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus

    # 计算攻击力
    @property
    def power_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus

    # 判断物品是否已装备
    def item_is_equipped(self, item: "Item") -> bool:
        return self.weapon == item or self.armor == item

    # 卸下装备消息
    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    # 装备消息
    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    # 装备到指定位置
    def equip_to_slot(self, slot: str, item: "Item", add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        # 将物品装备到指定位置
        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    # 从指定位置卸下装备
    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)

        # 将指定位置的物品设置为None
        setattr(self, slot, None)

    # 切换装备  
    def toggle_equip(self, equippable_item: "Item", add_message: bool = True) -> None:
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        else:
            slot = "armor"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)