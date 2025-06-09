from typing import Tuple

import numpy as np  # type: ignore

# 定义一个结构体类型 graphic_dt，用于描述每个地形的图形属性，兼容 tcod 控制台的 tiles_rgb。
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode 码点（字符）
        ("fg", "3B"),      # 前景色，3 个无符号字节，表示 RGB 颜色
        ("bg", "3B"),      # 背景色，3 个无符号字节，表示 RGB 颜色
    ]
)

# 定义地形结构体类型 tile_dt，用于静态描述每种地形的属性。
tile_dt = np.dtype(
    [
        ("walkable", np.bool_),      # 是否可行走
        ("transparent", np.bool_),   # 是否透明（影响视野/FOV）
        ("dark", graphic_dt),       # 不在视野内时的图形显示
        ("light", graphic_dt),      # 在视野内时的图形显示
    ]
)

# 定义一个辅助函数，用于创建新的地形类型
def new_tile(
    *,  # 强制使用关键字参数，保证参数顺序无关紧要
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """辅助函数，用于定义单个地形类型"""
    # 创建一个包含 walkable、transparent 和 dark 属性的 NumPy 数组  类型为 tile_dt
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD 代表未探索、未被看见的地块
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# 定义地板地形
floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)
# 定义墙壁地形
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50)),  
)

# 定义楼梯地形
down_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light=(ord(">"), (255, 255, 255), (200, 180, 50)),
)
