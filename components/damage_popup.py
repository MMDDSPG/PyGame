from typing import List, Tuple
import tcod
import time

class DamagePopup:
    def __init__(self, x: int, y: int, amount: int):
        self.x = x
        self.y = y
        self.amount = amount
        self.creation_time = time.time()
        self.duration = 0.5  # 显示0.5秒
        self.offset_y = 1    # 显示位置

    def is_expired(self) -> bool:
        return time.time() - self.creation_time > self.duration



class DamagePopupManager:
    def __init__(self):
        self.popups: List[DamagePopup] = []

    def add_popup(self, x: int, y: int, amount: int):
        self.popups.append(DamagePopup(x, y, amount))

    def update(self):
        # 移除过期的提示
        self.popups = [popup for popup in self.popups if not popup.is_expired()]
    

    def get_all_amounts(self, x, y):
        amounts = 0
        for popup in self.popups:
            if popup.x == x and popup.y == y:
                amounts += popup.amount
        return amounts

    def render(self, console: tcod.console.Console):
        self.update()

        for popup in self.popups:
            # 计算实际显示位置
            if popup.y > console.height // 2:
                display_y = max(int(popup.y - popup.offset_y), 0)
            else:
                display_y = min(int(popup.y + popup.offset_y), console.height - 1)

            allAmounts = self.get_all_amounts(popup.x, popup.y)

            # 显示伤害数值
            console.print(
                x=popup.x,
                y=display_y,
                string=f"{allAmounts}",
                fg=tcod.red
            )
            
            