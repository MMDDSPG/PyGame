from typing import Tuple


import copy
from typing import Tuple, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from game_map import GameMap

T = TypeVar("T", bound="Entity")

class Entity:
    """
    一个通用的对象，用于表示玩家、敌人、物品等。
    """
    def __init__(
       self,
       x: int = 0,
       y: int = 0,
       char: str = "?",
       color: Tuple[int, int, int] = (255, 255, 255),
       name: str = "<Unnamed>",
       blocks_movement: bool = False,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement

    # 创建一个实体的副本，并将其添加到地图中
    def spawn(self: T, gamemap: "GameMap", x: int, y: int) -> T:
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        gamemap.entities.add(clone)
        return clone

    # 移动实体
    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy