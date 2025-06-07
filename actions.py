from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING
import color
import exceptions

if TYPE_CHECKING:
   from engine import Engine
   from entity import Actor, Entity, Item

class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """返回此动作所属的引擎。"""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """使用确定其范围所需的对象执行此动作。

        `self.engine` 是执行此动作的范围。

        `self.entity` 是执行动作的对象。

        此方法必须由 Action 子类重写。
        """
        raise NotImplementedError()
    
class PickupAction(Action):
    """拾取物品并将其添加到物品栏中，如果有空间的话。"""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")

class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """返回此动作目标位置的角色。"""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """调用物品的能力，此动作将提供上下文。"""
        self.item.consumable.activate(self)

class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()

class DropItem(ItemAction):
    def perform(self) -> None:
        self.entity.inventory.drop(self.item)

class WaitAction(Action):
    def perform(self) -> None:
        pass

class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        如果楼梯存在，则移动到楼梯。
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")

# 移动或攻击的基类
class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """返回此动作的目标位置。"""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """返回此动作目标位置的阻挡实体。"""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)
    
    @property
    def target_actor(self) -> Optional[Actor]:
        """返回此动作目标位置的角色。"""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

# 攻击
class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        
        damage = self.entity.fighter.power - target.fighter.defense
        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(f"{attack_desc} for {damage} hit points.", attack_color)
            target.fighter.hp -= damage
        
        else:
            self.engine.message_log.add_message(f"{attack_desc} but does no damage.", attack_color)


# 移动
class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # 目标位置超出边界
            raise exceptions.Impossible("That way is blocked.")
        
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # 目标位置被地形阻挡
            raise exceptions.Impossible("That way is blocked.")
        

        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # 目标位置被实体阻挡
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)

# 移动或攻击
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        # 否则，进行移动
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()