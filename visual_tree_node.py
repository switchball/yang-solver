import random
from typing import Optional, List
from search.tree_node import TreeNode
from app.yang.logic.yang_tree_node import YangTreeNode
from app.yang.logic.yang_board_state import YangSimulatedState

class VisualTreeNode:
    node_id_counter = 0
    
    def __init__(self, real_node: TreeNode, parent: Optional['VisualTreeNode'] = None):
        self.id = VisualTreeNode.node_id_counter
        VisualTreeNode.node_id_counter += 1
        self.real_node = real_node
        self.parent = parent
        self.children: List['VisualTreeNode'] = []
        
        # 从真实节点同步统计数据
        self.visits = real_node.visits
        self.value = real_node.rewards
        self.q_value = real_node.rewards / real_node.visits if real_node.visits > 0 else 0.0
        
        # 从真实节点提取状态信息
        self.hidden_state = self._extract_state(real_node)
        self.action = real_node.action if hasattr(real_node, 'action') else None

    def _extract_state(self, node: YangTreeNode) -> dict:
        """从真实节点中提取状态信息"""
        state = node.state.get_hstate()._hstate
        return state
        state = {
            "step": 0,
            "current_player": "X",
            "board": [["-" for _ in range(3)] for _ in range(3)]
        }
        
        # 尝试从真实节点获取状态
        if hasattr(node, 'state'):
            try:
                # 从真实状态中提取数据
                state["step"] = node.state.step_count if hasattr(node.state, 'step_count') else 0
                state["current_player"] = getattr(node.state, 'current_player', "X")
                
                # 如果有棋盘状态，直接使用
                if hasattr(node.state, 'board_state'):
                    state["board"] = node.state.board_state
                else:
                    # 否则生成随机棋盘
                    state["board"] = [
                        [random.choice(["X", "O", "-"]) for _ in range(3)]
                        for _ in range(3)
                    ]
            except Exception as e:
                print(f"状态提取错误: {str(e)}")
        return state

    @property
    def winning_rate(self) -> float:
        return self.q_value

    def add_child(self, real_child_node: YangTreeNode) -> 'VisualTreeNode':
        child = VisualTreeNode(real_child_node, parent=self)
        self.children.append(child)
        return child

    def update_from_real_node(self):
        """从真实节点更新统计信息"""
        self.visits = self.real_node.visits
        self.value = self.real_node.rewards
        self.q_value = self.real_node.rewards / self.real_node.visits if self.real_node.visits > 0 else 0.0

    def is_fully_expanded(self) -> bool:
        return self.real_node.is_fully_expanded() if hasattr(self.real_node, 'is_fully_expanded') else len(self.children) > 0

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __repr__(self) -> str:
        return f"VisualNode(id={self.id}, visits={self.visits}, q={self.q_value:.2f}, win:{self.winning_rate:.1%})"
    
    @staticmethod
    def reset_node_counter():
        VisualTreeNode.node_id_counter = 0