# 导入 tcod 库，这是一个用于开发 Roguelike 游戏的 Python 库
import tcod

# 导入动作类
from actions import EscapeAction, MovementAction
from input_handlers import EventHandler

def main():
    # 设置游戏窗口的宽度和高度（以字符为单位）
    screen_width = 80
    screen_height = 50

    # 玩家初始位置
    player_x = int(screen_width / 2)
    player_y = int(screen_height / 2)

    # 加载游戏使用的字体图集
    # dejavu10x10_gs_tc.png: 字体文件
    # 32: 每行字符数
    # 8: 字符行数 
    # CHARMAP_TCOD: 使用 TCOD 的字符映射
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    # 创建事件处理器
    event_handler = EventHandler()

    # 创建游戏窗口
    # columns, rows: 窗口尺寸
    # tileset: 使用的字体图集
    # title: 窗口标题
    # vsync: 启用垂直同步，防止画面撕裂
    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="Yet Another Roguelike Tutorial",
        vsync=True,
    ) as context:
        # 创建主控制台对象
        # order="F" 表示使用 Fortran 风格的内存布局，这通常能提供更好的性能
        root_console = tcod.Console(screen_width, screen_height, order="F")
        
        # 创建事件处理器
        event_handler = EventHandler()
        
        # 游戏主循环
        while True:
            # 在控制台坐标 (1,1) 处打印 "@" 符号，这通常代表玩家角色
            root_console.print(x=player_x, y=player_y, string="@")

            # 将控制台内容渲染到屏幕上
            context.present(root_console)

            root_console.clear()

            # 事件处理循环
            for event in tcod.event.wait():
                # 如果检测到退出事件，则退出程序
                action = event_handler.dispatch(event)

                if action is None:
                    continue

                if isinstance(action, MovementAction):
                    player_x += action.dx
                    player_y += action.dy
                
                elif isinstance(action, EscapeAction):
                    raise SystemExit()

# Python 的标准入口点检查
# 确保代码只在直接运行时执行，而不是在被导入时执行
if __name__ == "__main__":
    main()