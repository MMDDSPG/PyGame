from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):
    parent: "Actor"

    def __init__(
        self,
        current_level: int = 1, #当前等级
        current_xp: int = 0, #当前经验值
        level_up_base: int = 0, #升级所需经验值
        level_up_factor: int = 150, #经验值增长系数
        xp_given: int = 0, #杀死敌人获得的经验值
    ):
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    # 计算升级所需经验值
    @property
    def experience_to_next_level(self) -> int:
        return self.level_up_base + self.current_level * self.level_up_factor

    # 判断是否需要升级
    @property
    def requires_level_up(self) -> bool:
        return self.current_xp > self.experience_to_next_level

    # 增加经验值
    def add_xp(self, xp: int) -> None:
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp

        self.engine.message_log.add_message(f"You gain {xp} experience points.")

        if self.requires_level_up:
            self.engine.message_log.add_message(
                f"You advance to level {self.current_level + 1}!"
            )

    # 增加等级
    def increase_level(self) -> None:
        self.current_xp -= self.experience_to_next_level

        self.current_level += 1

    # 增加最大生命值
    def increase_max_hp(self, amount: int = 20) -> None:
        self.parent.fighter.max_hp += amount
        self.parent.fighter.hp += amount

        self.engine.message_log.add_message("Your health improves!")

        self.increase_level()

    # 增加力量
    def increase_power(self, amount: int = 1) -> None:
        self.parent.fighter.base_power += amount

        self.engine.message_log.add_message("You feel stronger!")

        self.increase_level()

    # 增加防御
    def increase_defense(self, amount: int = 1) -> None:
        self.parent.fighter.base_defense += amount

        self.engine.message_log.add_message("Your movements are getting swifter!")

        self.increase_level()