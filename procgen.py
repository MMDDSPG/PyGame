import random
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod
import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


# 定义每个楼层最大物品数量 (楼层, 最大物品数量)
max_items_by_floor = [
   (1, 1),
   (4, 2),
]

# 定义每个楼层最大敌人数量 (楼层, 最大敌人数量)
max_monsters_by_floor = [
   (1, 2),
   (4, 3),
   (6, 5),
]

# 定义每个楼层物品概率 (楼层, 物品概率)
item_chances: Dict[int, List[Tuple["Entity", int]]] = {
   0: [(entity_factories.health_potion, 5)],
   2: [(entity_factories.confusion_scroll, 10)],
   4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5)],
   6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],
}

# 定义每个楼层敌人概率 (楼层, 敌人概率)
enemy_chances: Dict[int, List[Tuple["Entity", int]]] = {
   0: [(entity_factories.orc, 80)],
   3: [(entity_factories.troll, 15)],
   5: [(entity_factories.troll, 30)],
   7: [(entity_factories.troll, 60)],
}

egg_entity_by_floor: Dict[int, "Entity"] = {
    1: entity_factories.egg_C,
    2: entity_factories.egg_L,
    3: entity_factories.egg_Y,
    4: entity_factories.egg_S,
    5: entity_factories.egg_R,
    6: entity_factories.egg_K,
    7: entity_factories.egg_L,
}

def get_max_value_for_floor(
    weighted_chances_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in weighted_chances_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple["Entity", int]]],
    number_of_entities: int,
    floor: int,
) -> List["Entity"]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

            entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities

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

def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    print(f"Placing {number_of_monsters} monsters and {number_of_items} items on floor {floor_number}")

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )   

    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        isPlaced = False
        while not isPlaced:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
                entity.spawn(dungeon, x, y)
                isPlaced = True

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
    engine: "Engine",
) -> GameMap:
    """生成一个新的地牢地图。"""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []   

    center_of_last_room = (0, 0)
    new_room = None
    for r in range(max_rooms):
        isPlaced = False
        while not isPlaced:
            room_width = random.randint(room_min_size, room_max_size)
            room_height = random.randint(room_min_size, room_max_size)
            x = random.randint(0, dungeon.width - room_width - 1)
            y = random.randint(0, dungeon.height - room_height - 1)

            new_room = RectangularRoom(x, y, room_width, room_height)

            # 遍历其他房间，检查是否与当前房间重叠
            if any(new_room.intersects(other_room) for other_room in rooms):
                continue  # 有重叠则跳过，尝试下一个房间
            else:
                isPlaced = True
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

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        # 最后，把新房间加入房间列表
        rooms.append(new_room)

    # 随机选择一个房间放置彩蛋
    if engine.game_world.current_floor in egg_entity_by_floor:
        egg_entity = egg_entity_by_floor[engine.game_world.current_floor]
        room = random.choice(rooms)
        isPlaced = False
        while not isPlaced:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
                egg_entity.spawn(dungeon, x, y)
                isPlaced = True

    return dungeon