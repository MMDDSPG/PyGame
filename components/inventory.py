from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item


class Inventory(BaseComponent):
    parent: "Actor"

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List["Item"] = []

    def drop(self, item: "Item") -> None:
        """
        从物品栏中移除物品并将其恢复到游戏地图中，在玩家当前位置。
        """
        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        self.engine.message_log.add_message(f"You dropped the {item.name}.")