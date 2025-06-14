from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import color
import game_config

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from game_map import GameMap

def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()

def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)

    console.draw_rect(x=0, y=game_config.split_line_y + game_config.mouse_description, width=total_width, height=1, ch=1, bg=color.bar_empty)

    if bar_width > 0:
        console.draw_rect(
            x=0, 
            y=game_config.split_line_y + game_config.mouse_description, 
            width=bar_width, 
            height=1, 
            ch=1, 
            bg=color.bar_filled
        )

    console.print(
        x=1, 
        y=game_config.split_line_y + game_config.mouse_description, 
        string=f"HP: {current_value}/{maximum_value}", 
        fg=color.bar_text
    )

def render_dungeon_level(
    console: Console, dungeon_level: int, location: Tuple[int, int]
) -> None:
    """
    渲染玩家当前所在的层级，在给定的位置。
    """
    x, y = location

    console.print(x=x, y=y, string=f"Dungeon level: {dungeon_level}")

def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, string=names_at_mouse_location)

def render_margin(console: Console, x: int, y: int) -> None:
    console.draw_rect(x=x, y=y, width=game_config.screen_width, height=1, ch=1, bg=color.bar_empty)

def render_tip(console: Console, location: Tuple[int, int], tip: str) -> None:
    x, y = location
    console.print(x=x, y=y, string=tip)
