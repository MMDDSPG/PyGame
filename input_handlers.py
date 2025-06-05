from typing import Optional, TYPE_CHECKING

import tcod.event

from actions import Action, BumpAction, EscapeAction, WaitAction

if TYPE_CHECKING:
    from engine import Engine

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

class EventHandler:
    def __init__(self, engine: "Engine"):
        self.engine = engine

    def handle_events(self) -> None:
        raise NotImplementedError()
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        """
        处理退出事件
        当用户点击窗口关闭按钮时触发
        """
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
        return None
    

class MainGameEventHandler(EventHandler):
    """
    事件处理器协议类
    用于处理游戏中的各种输入事件，并将其转换为对应的游戏动作
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine

    def handle_events(self) -> None:
        for event in tcod.event.wait():
            action = self.dispatch(event)

            if action is None:
                continue

            action.perform()

            self.engine.handle_enemy_turns()
            self.engine.update_fov()  # 在玩家下一个动作之前更新 FOV。

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

        # 返回处理后的动作，如果没有匹配的按键则返回 None
        return action
    
class GameOverEventHandler(EventHandler):
    def handle_events(self) -> None:
        for event in tcod.event.wait():
            action = self.dispatch(event)

            if action is None:
                continue

            action.perform()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym

        if key == tcod.event.K_ESCAPE:
            action = EscapeAction(self.engine.player)

        # No valid key was pressed
        return action