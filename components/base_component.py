from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity
    from game_map import GameMap


class BaseComponent:
    parent: "Entity"  # 所属实体实例

    @property
    def gamemap(self) -> "GameMap":
        return self.parent.gamemap

    @property
    def engine(self) -> "Engine":
       return self.gamemap.engine