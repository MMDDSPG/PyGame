import random
from typing import Iterator, List, Tuple, TYPE_CHECKING

import tcod
import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine

class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """将这个房间的内部区域作为二维数组的索引返回"""
        # 返回一个包含两个切片对象的元组，分别表示行和列的切片范围
        # 切片对象用于从数组中提取子数组 即为房间中除去墙壁的区域
        # slice(self.x1 + 1, self.x2) 表示从 x1+1 到 x2-1 的切片
        # slice(self.y1 + 1, self.y2) 表示从 y1+1 到 y2-1 的切片
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)
    
    def intersects(self, other: "RectangularRoom") -> bool:
        """返回True如果这个房间与另一个RectangularRoom重叠"""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

def place_entities(
    room: RectangularRoom, dungeon: GameMap, maximum_monsters: int, maximum_items: int
) -> None:
    number_of_monsters = random.randint(0, maximum_monsters)
    number_of_items = random.randint(0, maximum_items)

    for i in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                entity_factories.troll.spawn(dungeon, x, y)

    for i in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.1:
                entity_factories.health_potion.spawn(dungeon, x, y)
            elif random.random() < 0.9:
                entity_factories.confusion_scroll.spawn(dungeon, x, y)
            else:
                entity_factories.lightning_scroll.spawn(dungeon, x, y)

def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """返回从这两个点之间绘制一个L形隧道"""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # 水平移动，然后垂直移动
        corner_x, corner_y = x2, y1
    else:
        # 垂直移动，然后水平移动
        corner_x, corner_y = x1, y2

    # 生成这个隧道的坐标
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    max_monsters_per_room: int,
    max_items_per_room: int,
    engine: "Engine",
) -> GameMap:
    """生成一个新的地牢地图。"""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []   

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # 遍历其他房间，检查是否与当前房间重叠
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # 有重叠则跳过，尝试下一个房间
        # 没有重叠则房间有效

        # 挖出这个房间的内部区域
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # 第一个房间，玩家的起始位置
            player.place(*new_room.center, dungeon)
        else:  # 之后的所有房间
            # 挖一条隧道连接当前房间和上一个房间
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)  

        # 最后，把新房间加入房间列表
        rooms.append(new_room)

    return dungeon