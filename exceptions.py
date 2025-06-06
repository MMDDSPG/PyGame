class Impossible(Exception):
    """当动作无法执行时引发的异常。

    原因作为异常消息给出。
    """

class QuitWithoutSaving(SystemExit):
    """用户选择退出游戏时引发的异常。"""