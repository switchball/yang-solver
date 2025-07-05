from copy import deepcopy
from PIL import Image

from app.yang.logic.yang_board_state import YangBoardState
from app.yang.logic.yang_tree_node import YangTreeNode
from app.yang.yang_yolo_recognizer import YangYOLORecognizer

from search.mcts import MCTS, example_rollout_policy

from test_rollout import step


class YangSimulator(object):
    def __init__(self):
        pass


def sample_rollout_policy(node: YangTreeNode):
    # looping num is outside the loop
    hstate_dict = node.state.get_hstate()._hstate
    hstate = deepcopy(hstate_dict)
    while not (is_terminal := step(hstate)):
        pass
        # print(".", end="")

    print("W" if hstate["queue_empty_slot"] == 7 else "L", f"Score: {hstate['score']}")
    # total_score += hstate["score"]
    return hstate["score"]

if __name__ == "__main__":
    full_image = Image.open("screenshot1.png")

    model_path = "runs/detect/train3/weights/best.pt"
    recognizer = YangYOLORecognizer(model_path)

    state = YangBoardState(full_image, last_hstate=None, simulator=recognizer)
    root = YangTreeNode(state=state)
    mcts = MCTS(root, rollout_policy=sample_rollout_policy, rollout_iterations=100, node_clz=YangTreeNode)

    mcts.run(30)

