from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod.event
import tcod.console
import actions
import os

from actions import (
    Action,
    BumpAction,
    EscapeAction,
    PickupAction,
    WaitAction
)
import color
import exceptions
import game_config
from loadImage import load_and_resize_image

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.KeySym.UP: (0, -1),
    tcod.event.KeySym.DOWN: (0, 1),
    tcod.event.KeySym.LEFT: (-1, 0),
    tcod.event.KeySym.RIGHT: (1, 0),
    tcod.event.KeySym.HOME: (-1, -1),
    tcod.event.KeySym.END: (-1, 1),
    tcod.event.KeySym.PAGEUP: (1, -1),
    tcod.event.KeySym.PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.KeySym.KP_1: (-1, 1),
    tcod.event.KeySym.KP_2: (0, 1),
    tcod.event.KeySym.KP_3: (1, 1),
    tcod.event.KeySym.KP_4: (-1, 0),
    tcod.event.KeySym.KP_6: (1, 0),
    tcod.event.KeySym.KP_7: (-1, -1),
    tcod.event.KeySym.KP_8: (0, -1),
    tcod.event.KeySym.KP_9: (1, -1),
    # Vi keys.
    tcod.event.KeySym.h: (-1, 0),
    tcod.event.KeySym.j: (0, 1),
    tcod.event.KeySym.k: (0, -1),
    tcod.event.KeySym.l: (1, 0),
    tcod.event.KeySym.y: (-1, -1),
    tcod.event.KeySym.u: (1, -1),
    tcod.event.KeySym.b: (-1, 1),
    tcod.event.KeySym.n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.KeySym.PERIOD,
    tcod.event.KeySym.KP_5,
    tcod.event.KeySym.CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.KeySym.RETURN,
    tcod.event.KeySym.KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]

class BaseEventHandler:
    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        
        assert not isinstance(state, Action), f"{self!r} can not handle actions."

        return self
    
    def on_render(self, console: tcod.console.Console) -> None:
        raise NotImplementedError()
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
    def dispatch(self, event: tcod.event.Event) -> Optional[Action]:
        """
        分发事件到对应的处理方法
        
        参数:
            event: 事件对象
        
        返回:
            对应的游戏动作，如果没有匹配的动作则返回 None
        """
        if isinstance(event, tcod.event.Quit):
            return self.ev_quit(event)
        elif isinstance(event, tcod.event.KeyDown):
            return self.ev_keydown(event)
        elif isinstance(event, tcod.event.MouseMotion):
            return self.ev_mousemotion(event)
        elif isinstance(event, tcod.event.MouseButtonDown):
            return self.ev_mousebuttondown(event)
        return None
    
def is_finish_Easter_eggs(engine: "Engine") -> bool:
    # 检查是否收集了所有彩蛋，且顺序正确
    target = ["Cai", "Le", "Yi", "Sheng", "Ri", "Kuai", "Le"]
    items = engine.player.inventory.items
    # 先判断数量
    if len(items) != len(target):
        return False
    # 依次比对名字
    for item, name in zip(items, target):
        if getattr(item, "name", None) != name:
            return False
    return True

class EventHandler(BaseEventHandler):
    def __init__(self, engine: "Engine"):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            if not self.engine.player.is_alive:
                return GameOverEventHandler(self.engine)
            elif self.engine.game_world.current_floor > 7:
                if is_finish_Easter_eggs(self.engine):
                    return PopupMessage(parent_handler=GameOverEventHandler(self.engine), text="", needQuit= True, bgStr="assets/birthday.png")
                else:
                    return PopupMessage(parent_handler=GameOverEventHandler(self.engine), text="You win!", needQuit= True)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)
        return self
    
    def handle_action(self, action: Optional[Action]) -> bool:
        """处理从事件方法返回的动作。
        如果动作会推进一个回合则返回True。"""

        if action is None:
            return False
        
        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # 发生异常时跳过敌人回合
        self.engine.handle_enemy_turns()
        self.engine.update_fov()

        return True


    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
           self.engine.mouse_location = event.tile.x, event.tile.y
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        raise NotImplementedError()
    
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        # raise NotImplementedError()
        pass

class MainGameEventHandler(EventHandler):
    """
    事件处理器协议类
    用于处理游戏中的各种输入事件，并将其转换为对应的游戏动作
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """
        处理键盘按下事件
        将键盘输入转换为对应的游戏动作
        
        参数:
            event: 键盘事件对象，包含按键信息
        
        返回:
            对应的游戏动作，如果没有匹配的动作则返回 None
        """
        # 初始化动作为 None
        action: Optional[Action] = None

        # 获取按下的键
        key = event.sym

        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.KeySym.PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        # 处理 ESC 键，创建退出动作
        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction(player)
        elif key == tcod.event.KeySym.v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.KeySym.g:
            action = PickupAction(player)
        elif key == tcod.event.KeySym.i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.KeySym.d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.KeySym.c:
           return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.KeySym.SLASH:
            return LookHandler(self.engine)
            
        # 返回处理后的动作，如果没有匹配的按键则返回 None
        return action
    
class GameOverEventHandler(EventHandler):

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.KeySym.ESCAPE:
            self.on_quit()
    
CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
    tcod.event.KeySym.PAGEUP: -10,
    tcod.event.KeySym.PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """在可导航的较大窗口中打印历史记录。"""

    def __init__(self, engine: "Engine"):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)  # 将主状态绘制为背景

        log_console = tcod.console.Console(console.width - 6, console.height - 6)

        # 绘制带有自定义横幅标题的框架
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print(
            x=log_console.width // 2,
            y=0,
            string="┤History├",
            alignment=tcod.constants.CENTER
        )

        # 使用光标参数渲染消息日志
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        # 花哨的条件移动，使其感觉正确
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # 只有在边缘时才从顶部移动到底部
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # 同样适用于从底部到顶部的移动
                self.cursor = 0
            else:
                # 否则在保持限制在历史日志边界内的情况下移动
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0  # 直接移动到顶部消息
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1  # 直接移动到最后一条消息
        else:  # 任何其他键都会返回到主游戏状态
            return MainGameEventHandler(self.engine)
        
        return None

class AskUserEventHandler(EventHandler):
    """处理需要特殊输入的动作的用户输入。"""
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """默认情况下，任何键都会退出此输入处理器。"""
        if event.sym in {  # 忽略修饰键
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()
    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)
    
class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)

        width = len(self.TITLE) + 8

        if self.engine.player.x <= game_config.screen_width // 2:
            x = game_config.screen_width - width - game_config.x_margin
        else:
            x = game_config.x_margin

        y = 0
        height = 7

        console.draw_frame(x=x,y=y,width=width,height=height)
        console.print(
            x=x + width // 2,
            y=y,
            string=self.TITLE,
            alignment=tcod.constants.CENTER
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1, y=y + 4, string=f"Attack: {self.engine.player.fighter.power} (Equipped: {self.engine.player.equipment.power_bonus})"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Defense: {self.engine.player.fighter.defense} (Equipped: {self.engine.player.equipment.defense_bonus})"
        )
    
# 升级事件处理
class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)

        width = 40
        height = 8

        if self.engine.player.x <= game_config.screen_width // 2:
            x = game_config.screen_width - width - game_config.x_margin
        else:
            x = game_config.x_margin

        y = 0
        

        console.draw_frame(x=x,y=y,width=width,height=height)
        console.print(
            x=x + width // 2,
            y=y,
            string=self.TITLE,
            alignment=tcod.constants.CENTER
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x + 1,
            y=4,
            string=f"a) Constitution (+20 HP, from {self.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Strength (+1 attack, from {self.engine.player.fighter.power})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Agility (+1 defense, from {self.engine.player.fighter.defense})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None
    
class InventoryEventHandler(AskUserEventHandler):
    """此处理器让用户选择一个物品。

    然后发生的事情取决于子类。
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.console.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3       

        # 计算标题的宽度
        title_width = len(self.TITLE)
        # 计算最长的物品名称长度
        max_item_width = max(
            (len(item.name) for item in self.engine.player.inventory.items),
            default=0
        )
        # 物品名称前需要加上 "(a) " 这样的前缀，所以加4 (E) 再加4
        width = max(title_width, max_item_width + 4) + 4 + 4

        if self.engine.player.x <= game_config.screen_width // 2:
            x = game_config.screen_width - width - game_config.x_margin
        else:
            x = game_config.x_margin

        y = 0


        console.draw_frame(x=x,y=y,width=width,height=height)
        console.print(
            x=x + width // 2,
            y=y,
            string=self.TITLE,
            alignment=tcod.constants.CENTER
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                is_equipped = self.engine.player.equipment.item_is_equipped(item)
                item_string = f"({item_key}) {item.name}"
                if is_equipped:
                    item_string = f"{item_string} (E)"
                console.print(x + 1, y + i + 1, item_string)

        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: "Item") -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()
    
class InventoryActivateHandler(InventoryEventHandler):
    """处理使用物品栏中的物品。"""

    TITLE = "Use Item"

    def on_item_selected(self, item: "Item") -> Optional[ActionOrHandler]:
        """Return the action for the selected item."""
        if item.consumable:
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return item.equippable.get_action(self.engine.player)
        else:
            return None
    
class InventoryDropHandler(InventoryEventHandler):
    """处理丢弃物品栏中的物品。"""

    TITLE = "Drop Item"

    def on_item_selected(self, item: "Item") -> Optional[ActionOrHandler]:
        """Drop this item."""
        return actions.DropItem(self.engine.player, item)
    
# 选择地图位置
class SelectIndexHandler(AskUserEventHandler):
    """处理用户选择一个地图地点。"""

    def __init__(self, engine: "Engine"):
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.console.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.rgb["bg"][x, y] = color.white
        console.rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """检查按键是否移动或确认按键"""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1 
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20
                
            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None

        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        
        return super().ev_keydown(event)
    
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """鼠标点击事件"""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
            
        return super().ev_mousebuttondown(event)


    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """当用户选择一个位置时调用"""
        raise NotImplementedError()
    
# 查看位置
class LookHandler(SelectIndexHandler):
    """处理查看位置的请求。"""
    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)

# 单次远程选择攻击
class SingleRangedAttackHandler(SelectIndexHandler):
    """处理针对单个敌人的操作。只有选定的敌人会受到影响"""
    def __init__(self, engine: "Engine", callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__(engine)
        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))
        
# 范围远程选择攻击
class AreaRangedAttackHandler(SelectIndexHandler):
    """处理范围远程选择攻击"""
    def __init__(self, engine: "Engine", radius: int , callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__(engine)
        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.console.Console) -> None:
        """高亮选中的区域"""
        super().on_render(console)
        x, y = self.engine.mouse_location

        for c_x in range(x - self.radius - 1, x + self.radius + 1):
            for c_y in range(y - self.radius - 1, y + self.radius + 1):
                if (c_x - x) ** 2 + (c_y - y) ** 2 <= self.radius ** 2:
                    console.rgb["bg"][c_x, c_y] = color.red

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, *, parent_handler: BaseEventHandler, text: str, needQuit: bool = False, bgStr: str = ""):
        self.parent = parent_handler
        self.text = text
        self.needQuit = needQuit
        self.bgStr = bgStr

    def on_render(self, console: tcod.console.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8

        if (self.bgStr):
            background_image = load_and_resize_image(self.bgStr, game_config.screen_width * 2, game_config.screen_height * 2)
            console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        if (self.needQuit):
            raise SystemExit()
        return self.parent
