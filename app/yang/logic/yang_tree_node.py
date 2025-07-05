from copy import deepcopy

from app.yang.logic.yang_board_state import YangSimulatedState

from search.tree_node import TreeNode


class YangTreeNode(TreeNode):
    def __init__(self, state: YangSimulatedState, action=None):
        super().__init__(state, action)
        self.prev_state = None
        if action is not None:
            self.prev_state = state
            self.state = YangSimulatedState(
                self.prev_state.get_crt_img(), 
                last_hstate=deepcopy(self.prev_state.get_hstate()),  # deepcopy?
                simulator=self.prev_state.simulator,
                pending_action=action
            )

        self.visited_action_mask = None

    def get_possible_actions(self):
        # override
        actions = self.state.find_available_actions()
        return actions

    def get_action_weights(self):
        # override
        return self.state.get_action_prior_weights(self.get_possible_actions())

