import random
import math
from collections import defaultdict

from search.tree_node import TreeNode


class MCTS:
    def __init__(self, root_node: TreeNode, rollout_policy, rollout_iterations=1, node_clz=TreeNode):
        self.root_node = root_node
        self.rollout_policy = rollout_policy
        self.rollout_iterations = rollout_iterations
        self.node_clz = node_clz
        self.children = {}
        self.parent = {}

    def _uct_select(self, node):
        # All children of node should already be expanded:
        assert all(n.is_visited() for n in self.children[node])

        # 使用UCB1公式选择子节点
        c = math.sqrt(2)
        return max(self.children[node], key=lambda x: x.rewards / x.visits + c * math.sqrt(math.log(node.visits) / x.visits))

    def _select(self, node):
        """从根节点开始, 向下寻找一个可展开的子节点"""
        path = []
        while True:
            path.append(node)
            # if node not in self.children or not self.children[node]:
            if node not in self.children or node.is_terminal():
                # node is either unexplored or terminal
                return path
            # 检查是否存在未被尝试过的子节点
            visited_action_mask = {child.action for child in self.children[node]}
            unexplored = set(node.available_actions) - visited_action_mask
            if unexplored:
                action = self.sample_action_from_node(node, visited_action_mask)
                child_node = self.node_clz(state=node.state, action=action)
                self.children[node].append(child_node)
                self.parent[child_node] = node
                path.append(child_node)
                return path
            node = self._uct_select(node)  # descend a layer deeper

    def sample_action_from_node(self, node: TreeNode, visited_action_mask):
        actions, weights = node.available_actions_and_weights
        for k in range(len(actions)):
            if actions[k] in visited_action_mask:
                weights[k] = 0
        # 根据权重进行采样
        return random.choices(actions, weights=weights, k=1)[0]

    def expand_node(self, node):
        # 若第一次遇到该节点，则不扩展，而是直接计算 rollout
        if node.is_visited():
            node.expand_for_next_actions()
            return True
        if node in self.children and len(self.children[node]) > 0:
            assert False, f"node {node} has been expanded before, has {len(self.children[node])} children"
        self.children[node] = []
        return False


    def simulate(self, node):
        # 从当前节点开始进行模拟
        total_reward = 0
        for _ in range(self.rollout_iterations):
            total_reward += self.rollout_policy(node)
        return total_reward / self.rollout_iterations

    def backpropagate(self, node, reward):
        # 反向传播结果
        while node is not None:
            node.visits += 1
            node.rewards += reward
            node = self.parent.get(node, None)

    def best_child(self, node):
        # 选择最佳子节点，使用平均回报
        print("Best child key", [x.action for x in self.children[node]])
        print("Best child rwd", [x.rewards / x.visits for x in self.children[node]])
        print("Best child visits", [x.visits for x in self.children[node]])
        return max(self.children[node], key=lambda x: x.rewards / x.visits)

    def stats(self):
        mean_rwd = [x.rewards / x.visits for x in self.children[self.root_node]]
        visits = [x.visits for x in self.children[self.root_node]]
        import numpy as np
        max_idx = np.array(mean_rwd).argmax()
        return f"Rwd: {mean_rwd}\nVisits: {visits}\nMaxIdx: {max_idx}"

    def run(self, iterations):
        for iter_idx in range(iterations):
            path = self._select(self.root_node)
            leaf_node = path[-1]
            self.expand_node(leaf_node)
            reward = self.simulate(leaf_node)
            self.backpropagate(leaf_node, reward)
            print(f"MCTS Iteration {iter_idx} path: {path} reward: {reward}")
        return self.best_child(self.root_node)


# 示例 rollout policy
def example_rollout_policy(node):
    # 这里需要根据具体问题定义模拟过程
    # 例如，在棋盘游戏中，可能是随机进行游戏直到结束
    return random.random()  # 示例奖励

# 示例使用
if __name__ == "__main__":
    root = TreeNode(state="root")
    mcts = MCTS(root, rollout_policy=example_rollout_policy, rollout_iterations=10)
    best_child = mcts.run(10)
    print(f"Best action: {best_child.action}")
    print(f"MCTS Children: {mcts.children}")