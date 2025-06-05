# 导入 tcod 库，这是一个用于开发 Roguelike 游戏的 Python 库
import tcod

import copy

# 导入动作类
from engine import Engine
from input_handlers import EventHandler
import entity_factories
from procgen import generate_dungeon

def main():
    # 设置游戏窗口的宽度和高度（以字符为单位）
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 45

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2

    # 加载游戏使用的字体图集
    # dejavu10x10_gs_tc.png: 字体文件
    # 32: 每行字符数
    # 8: 字符行数 
    # CHARMAP_TCOD: 使用 TCOD 的字符映射
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    # 创建玩家
    player = copy.deepcopy(entity_factories.player)

    # 创建引擎
    engine = Engine(player=player)
    

    # 创建游戏地图
    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        engine=engine
    )

    engine.update_fov()

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
        
        # 游戏主循环
        while True:
           
            engine.render(console=root_console, context=context)

            engine.event_handler.handle_events()

            root_console.clear()

# Python 的标准入口点检查
# 确保代码只在直接运行时执行，而不是在被导入时执行
if __name__ == "__main__":
    main()