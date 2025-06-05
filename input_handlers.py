from typing import Optional

import tcod.event

from actions import Action, BumpAction, EscapeAction


class EventHandler:
    """
    事件处理器协议类
    用于处理游戏中的各种输入事件，并将其转换为对应的游戏动作
    """
    
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

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        """
        处理退出事件
        当用户点击窗口关闭按钮时触发
        """
        raise SystemExit()

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

        # 根据不同的按键创建对应的移动动作
        if key == tcod.event.K_UP:  # 上方向键
            action = BumpAction(dx=0, dy=-1)  # 向上移动
        elif key == tcod.event.K_DOWN:  # 下方向键
            action = BumpAction(dx=0, dy=1)   # 向下移动
        elif key == tcod.event.K_LEFT:  # 左方向键
            action = BumpAction(dx=-1, dy=0)  # 向左移动
        elif key == tcod.event.K_RIGHT:  # 右方向键
            action = BumpAction(dx=1, dy=0)   # 向右移动

        # 处理 ESC 键，创建退出动作
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction()

        # 返回处理后的动作，如果没有匹配的按键则返回 None
        return action