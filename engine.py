from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov


from input_handlers import EventHandler


if TYPE_CHECKING:
    from entity import Entity
    from game_map import GameMap

class Engine:

    game_map: "GameMap"

    def __init__(self, player: "Entity"):
        self.event_handler: EventHandler = EventHandler(self)
        self.player = player

    def handle_enemy_turns(self) -> None:
        # 遍历地图中的所有实体，除了玩家
        for entity in self.game_map.entities - {self.player}:
            print(f'The {entity.name} wonders when it will get to take a real turn.')

    def update_fov(self) -> None:
        """重计算玩家视野范围内的可见区域。"""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # 如果一个方块在 "visible" 数组中，则它应该被添加到 "explored" 数组中。
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console, context: Context) -> None:
        self.game_map.render(console)

        context.present(console)

        console.clear()