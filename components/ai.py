from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction


if TYPE_CHECKING:
    from entity import Actor

class BaseAI(Action):
    entity: Actor

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """计算并返回到目标位置的路径.

        如果没有有效路径，则返回空列表。
        """
        # 复制可行走的数组。
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # 检查实体是否阻挡移动并且成本不为零（阻挡）。
            if entity.blocks_movement and cost[entity.x, entity.y]:
                cost[entity.x, entity.y] += 10

        # 从成本数组创建一个图，并将其传递给新的路径查找器。
        # 表示上下左右移动的成本为2
        # 表示对角线移动的成本为3
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # 起始位置。

        # 计算到目标位置的路径并删除起始点。
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # 从 List[List[int]] 转换为 List[Tuple[int, int]]。
        return [(index[0], index[1]) for index in path]
    
class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # 切比雪夫距离

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()
    
class ConfusedEnemy(BaseAI):
    """一个困惑的敌人会随机移动。"""
    def __init__(self, entity: "Actor", previous_ai: Optional[BaseAI], turns_remaining: int):
        super().__init__(entity)
        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining
        
    def perform(self) -> None:
        """随机移动。"""
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                "The {self.entity.name} is no longer confused.")
            self.entity.ai = self.previous_ai
        else:
            # 随机选择一个方向
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )
            self.turns_remaining -= 1
            # 演员可能会尝试在选定的随机方向移动或攻击。
            # 演员可能会在墙上撞到墙，浪费一个回合。
            return BumpAction(self.entity, direction_x, direction_y,).perform()