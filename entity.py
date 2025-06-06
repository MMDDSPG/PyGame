import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from game_map import GameMap

T = TypeVar("T", bound="Entity")

class Entity:
    """
    一个通用的对象，用于表示玩家、敌人、物品等。
    """
    parent: Union["GameMap", "Inventory"]

    def __init__(
       self,
       parent: Optional["GameMap"] = None,
       x: int = 0,
       y: int = 0,
       char: str = "?",
       color: Tuple[int, int, int] = (255, 255, 255),
       name: str = "<Unnamed>",
       blocks_movement: bool = False,
       render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if parent:
            # 如果游戏地图现在没有提供，稍后会设置
            self.gamemap = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> "GameMap":
        return self.parent.gamemap

    # 创建一个实体的副本，并将其添加到地图中
    def spawn(self: T, gamemap: "GameMap", x: int, y: int) -> T:
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    # 移动实体
    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

    def place(self, x: int, y: int, gamemap: Optional["GameMap"] = None) -> None:
        """将实体放置在新位置。处理跨游戏地图的移动。"""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"): 
                if self.parent is self.gamemap: # 可能未初始化
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """返回这个实体和给定坐标之间的距离。"""
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        

class Actor(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type["BaseAI"],
        fighter: "Fighter",
        inventory: "Inventory",
    ):
        super().__init__(
           x=x,
           y=y,
           char=char,
           color=color,
           name=name,
           blocks_movement=True,
           render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional["BaseAI"] = ai_cls(self)

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

    @property
    def is_alive(self) -> bool:
       """只要这个角色还能执行动作就返回True。"""
       return bool(self.ai)
    
class Item(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        consumable: "Consumable",
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        self.consumable = consumable
        self.consumable.parent = self
    