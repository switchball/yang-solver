

class TreeNode:
    def __init__(self, state, action=None):
        self.state = state
        self.action = action
        self.visits = 0
        self.rewards = 0.0
        self._available_actions = None
        self._action_weights = None

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
        return len(self.untried_actions) == 0

    def is_visited(self):
        return self.visits > 0