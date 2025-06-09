import numpy as np  # type: ignore
from tcod.console import Console

from entity import Actor, Item
import tile_types

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

if TYPE_CHECKING:
   from engine import Engine
   from entity import Entity

class GameMap:
    def __init__(
        self, engine: "Engine", width: int, height: int, entities: Iterable["Entity"] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.entities = set(entities)

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # 玩家目前视野范围内可见的地图格子
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # 玩家之前探索过的地图格子

        self.downstairs_location = (0, 0)
    
    @property
    def gamemap(self) -> "GameMap":
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """遍历地图上所有存活的角色。"""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional["Entity"]:
        for entity in self.entities:
            if (
                entity.blocks_movement
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity

        return None
    
    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """如果x和y在地图边界内则返回True。"""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        渲染地图。
        如果一个方块在 "visible" 数组中，则用 "light" 颜色绘制它。
        如果它不在 "visible" 数组中，但它在 "explored" 数组中，则用 "dark" 颜色绘制它。
        否则，默认是 "SHROUD"。
        """
        console.rgb[0:self.width, 0:self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value       
        )

        for entity in entities_sorted_for_rendering:
            # 只打印在视野范围内的实体
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)

class GameWorld:
    """
    保存 GameMap 的设置，并在移动到楼梯时生成新地图。
    """

    def __init__(
        self,
        *,
        engine: "Engine",
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

    def generate_floor(self) -> None:
        from procgen import generate_dungeon
        # 生成新的地图
        self.current_floor += 1

        self.engine.game_map = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine,
        )