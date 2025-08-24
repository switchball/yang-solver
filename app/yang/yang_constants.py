import math
# 一些常量定义

CARD_KINDS = 16  # 卡片的种类数目

MAIN_AREA_POSITION = (0.05, 0.19, 0.9, 0.68)  # 棋盘主要区域坐标 (x, y, w, h)

VERBOSE = False  # 是否打印详细信息

# MCTS 算法相关
MCTS_RUN_ITERATION = 300 // 3
MCTS_ROLLOUT_BATCH_SIZE = 2
MCTS_CONFIDENCE = 3 * math.sqrt(15)

RWD_NON_CRITICAL_ACTION = -0.9
RWD_IS_CRITICAL_ACTION = 0.5

# 核心选区配置
# 使用 flet_label_region.py 进行选区标注，可以配置多个，每行一个，尽量不要重叠
# 配置格式为：(x, y, w, h) i.e. (left, top, width, height) 
CRITIC_AREA_CONFIG = [
    (0.264, 0.197, 0.477, 0.411),  # (x, y, w, h)
]
