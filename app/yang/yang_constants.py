# 一些常量定义

CARD_KINDS = 16  # 卡片的种类数目

MAIN_AREA_POSITION = (0.05, 0.19, 0.9, 0.68)  # 棋盘主要区域坐标 (x, y, w, h)

VERBOSE = False  # 是否打印详细信息

# MCTS 算法相关
MCTS_RUN_ITERATION = 80
MCTS_ROLLOUT_BATCH_SIZE = 16

RWD_NON_CRITICAL_ACTION = -1.5
RWD_IS_CRITICAL_ACTION = 0.3

# 核心选区配置
# 使用 flet_label_region.py 进行选区标注，可以配置多个，每行一个，尽量不要重叠
# 配置格式为：(x, y, w, h) i.e. (left, top, width, height) 
CRITIC_AREA_CONFIG = [
    (0.319, 0.201, 0.366, 0.235),  # (x, y, w, h)
]
