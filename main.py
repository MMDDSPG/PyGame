# 导入 tcod 库，这是一个用于开发 Roguelike 游戏的 Python 库
import tcod
import color
import traceback
import exceptions
import input_handlers
import setup_game

def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")

def main():
    # 设置游戏窗口的宽度和高度（以字符为单位）
    screen_width = 80
    screen_height = 50

    # 加载游戏使用的字体图集
    # dejavu10x10_gs_tc.png: 字体文件
    # 32: 每行字符数
    # 8: 字符行数 
    # CHARMAP_TCOD: 使用 TCOD 的字符映射
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

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
        root_console = tcod.console.Console(screen_width, screen_height, order="F")
        
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            # TODO: Add the save function here
            save_game(handler, "savegame.sav")
            raise
        except BaseException:  # Save on any other unexpected exception.
            # TODO: Add the save function here
            save_game(handler, "savegame.sav")
            raise
                        

# Python 的标准入口点检查
# 确保代码只在直接运行时执行，而不是在被导入时执行
if __name__ == "__main__":
    main()