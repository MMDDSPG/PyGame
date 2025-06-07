from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import render_functions
from message_log import MessageLog

import exceptions

import lzma
import pickle


if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld

class Engine:

    game_map: "GameMap"
    game_world: "GameWorld"

    def __init__(self, player: "Actor"):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        # 遍历地图中的所有实体，除了玩家
        for entity in set(self.game_map.actors) - {self.player}:
           if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """重计算玩家视野范围内的可见区域。"""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # 如果一个方块在 "visible" 数组中，则它应该被添加到 "explored" 数组中。
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)  
