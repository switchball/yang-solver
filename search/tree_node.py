

class TreeNode:
    def __init__(self, state, action=None):
        self.state = state
        self.action = action
        self.visits = 0
        self.rewards = 0.0
        self._best_q = float("-inf")
        self._rollout_q = None
        self._best_q_without_rollout = float("-inf")
        self._available_actions = None
        self._action_weights = None
        self._tried_action_num = 0

    def is_terminal(self):
        """判断当前节点是否是目标节点"""
        return False

    def expand_for_next_actions(self):
        """对节点展开，这通常意味着要计算其所有可用的动作"""
        self._expanded = True
        if self._available_actions is None:
            self._available_actions = self.get_possible_actions()
            self._action_weights = self.get_action_weights()

    @property
    def available_actions(self):
        if self._available_actions is None:
            self.expand_for_next_actions()
        return self._available_actions

    @property
    def available_actions_and_weights(self):
        return self._available_actions, self._action_weights

    def get_possible_actions(self):
        # 这里需要根据具体问题定义可能的动作
        # 例如，在棋盘游戏中，可能是所有合法的走法
        return [1, 2, 3]  # 示例动作

    def get_action_weights(self):
        # 这里需要根据具体问题定义动作的权重
        # 例如，可以是每个动作的先验概率
        return [1.0, 1.0, 1.0]  # 示例权重

    def is_fully_expanded(self):
        return self._available_actions is not None and len(self._available_actions) <= self._tried_action_num

    def is_visited(self):
        return self.visits > 0
    
    def increase_tried_action_num(self):
        self._tried_action_num += 1
    
    @property
    def best_q(self):
        """返回子节点的最优 Q 值
        
        如果子节点没有被完全探索，初次 rollout_q 也计入其中
        如果子节点已经全部探索完，则取所有子节点"""
        return self._best_q

    def set_best_q(self, q: float):
        """设置子节点的最优 Q 值"""
        self._best_q = q

    # def update_q(self, reward: float, is_fully_explored: bool):
    #     """更新 Q 值"""
    #     # 第一次更新
    #     if self._rollout_q is None:
    #         self._rollout_q = reward
    #         self.best_q = self._rollout_q
    #     # 后续的更新
    #     else:
    #         self._best_q_without_rollout = max(self._best_q_without_rollout, reward)
    #         self.best_q = max(self.best_q, self._best_q_without_rollout)
        
    #     # 如果节点已探索，则忽略 rollout_q 的值，除非第一次就探索到了叶子节点
    #     if is_fully_explored and self._best_q_without_rollout != float("-inf"):
    #         self.best_q = self._best_q_without_rollout
