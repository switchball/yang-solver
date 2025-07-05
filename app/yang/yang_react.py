from copy import deepcopy

from app.yang.logic.yang_board_state import YangBoardState
from app.yang.logic.yang_tree_node import YangTreeNode
from app.yang.yang_constants import (
    MCTS_RUN_ITERATION, RWD_NON_CRITICAL_ACTION, MCTS_ROLLOUT_BATCH_SIZE, RWD_IS_CRITICAL_ACTION
)

from controller.react.base_react import BaseReact
from controller.recognize.maybe_result import MaybeResult
from controller.react.gui_action import GUIAction

from search.mcts import MCTS
from test_rollout import step


def fast_rollout_policy(node: YangTreeNode):
    # looping num is outside the loop
    hstate_dict = node.state.get_hstate()._hstate
    if hasattr(node.state, "pending_action") and node.state.pending_action:
        pending_action = node.state.pending_action
        is_critical_action = pending_action[7]
        action_rwd = RWD_NON_CRITICAL_ACTION if not is_critical_action else RWD_IS_CRITICAL_ACTION
    else:
        action_rwd = 0
    hstate = deepcopy(hstate_dict)
    while not (is_terminal := step(hstate)):
        pass
        # print(".", end="")

    # print("W" if hstate["queue_empty_slot"] == 7 else "L", f"Score: {hstate['score']}")
    # total_score += hstate["score"]
    return hstate["score"] + action_rwd


class YangReact(BaseReact):
    def __init__(self):
        pass

    def react(self, result: MaybeResult) -> GUIAction:
        state = result.result  # type: YangBoardState
        root = YangTreeNode(state=state)

        # Construct Monte Carlo Tree Search
        self.mcts = MCTS(
            root,
            rollout_policy=fast_rollout_policy,
            rollout_iterations=MCTS_ROLLOUT_BATCH_SIZE,
            node_clz=YangTreeNode
        )
        child_node = self.mcts.run(MCTS_RUN_ITERATION)

        print("node", child_node, child_node.action)
        
        return child_node

        #     return BaseReact.GUIAction.NONE
        # else:
        #     return BaseReact.GUIAction.RETRY