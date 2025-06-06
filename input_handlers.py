from typing import Callable, Optional, Tuple, TYPE_CHECKING

import tcod.event
import actions

from actions import (
    Action,
    BumpAction,
    EscapeAction,
    PickupAction,
    WaitAction
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
     # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

class EventHandler:
    def __init__(self, engine: "Engine"):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))
    
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
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        """
        处理退出事件
        当用户点击窗口关闭按钮时触发
        """
        raise SystemExit()
    
    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        raise NotImplementedError()
    
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        # raise NotImplementedError()
        pass
    
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
    

class MainGameEventHandler(EventHandler):
    """
    事件处理器协议类
    用于处理游戏中的各种输入事件，并将其转换为对应的游戏动作
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
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

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        # 处理 ESC 键，创建退出动作
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction(player)
        elif key == tcod.event.K_v:
            self.engine.event_handler = HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            self.engine.event_handler = InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            self.engine.event_handler = InventoryDropHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            self.engine.event_handler = LookHandler(self.engine)
            
        # 返回处理后的动作，如果没有匹配的按键则返回 None
        return action
    
class GameOverEventHandler(EventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            raise SystemExit()
    
CURSOR_Y_KEYS = {
   tcod.event.K_UP: -1,
   tcod.event.K_DOWN: 1,
   tcod.event.K_PAGEUP: -10,
   tcod.event.K_PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """在可导航的较大窗口中打印历史记录。"""

    def __init__(self, engine: "Engine"):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # 将主状态绘制为背景

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # 绘制带有自定义横幅标题的框架
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤消息历史├", alignment=tcod.CENTER
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

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
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
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # 直接移动到顶部消息
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # 直接移动到最后一条消息
        else:  # 任何其他键都会返回到主游戏状态
            self.engine.event_handler = MainGameEventHandler(self.engine)

class AskUserEventHandler(EventHandler):
    """处理需要特殊输入的动作的用户输入。"""

    def handle_action(self, action: Optional[Action]) -> bool:
        """当执行了有效动作时返回到主事件处理器。"""
        if super().handle_action(action):
            self.engine.event_handler = MainGameEventHandler(self.engine)
            return True
        return False

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        """默认情况下，任何键都会退出此输入处理器。"""
        if event.sym in {  # 忽略修饰键
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[Action]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return None
    
class InventoryEventHandler(AskUserEventHandler):
    """此处理器让用户选择一个物品。

    然后发生的事情取决于子类。
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x + 1, y + i + 1, f"({item_key}) {item.name}")
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: "Item") -> Optional[Action]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()
    
class InventoryActivateHandler(InventoryEventHandler):
    """处理使用物品栏中的物品。"""

    TITLE = "选择要使用的物品"

    def on_item_selected(self, item: "Item") -> Optional[Action]:
        """Return the action for the selected item."""
        return item.consumable.get_action(self.engine.player)
    
class InventoryDropHandler(InventoryEventHandler):
    """处理丢弃物品栏中的物品。"""

    TITLE = "选择要丢弃的物品"

    def on_item_selected(self, item: "Item") -> Optional[Action]:
        """Drop this item."""
        return actions.DropItem(self.engine.player, item)
    
# 选择地图位置
class SelectIndexHandler(AskUserEventHandler):
    """处理用户选择一个地图地点。"""

    def __init__(self, engine: "Engine"):
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.rgb["bg"][x, y] = color.white
        console.rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
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
    
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        """鼠标点击事件"""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
            
        return super().ev_mousebuttondown(event)


    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """当用户选择一个位置时调用"""
        raise NotImplementedError()
    
# 查看位置
class LookHandler(SelectIndexHandler):
    """处理查看位置的请求。"""
    def on_index_selected(self, x: int, y: int) -> None:
        """Return to main handler."""
        self.engine.event_handler = MainGameEventHandler(self.engine)

# 单次远程选择攻击
class SingleRangedAttackHandler(SelectIndexHandler):
    """处理针对单个敌人的操作。只有选定的敌人会受到影响"""
    def __init__(self, engine: "Engine", callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__(engine)
        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))
        