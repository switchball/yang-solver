from app.yang.img_utils import image_overlay
from app.yang.yang_hstate import YangHiddenState


class YangBoardState(object):
    def __init__(self, board_img, last_hstate, simulator):
        self.board_img = board_img
        self._last_hstate = last_hstate
        self._cached_hstate = None
        self._cached_pool_cards = None
        self._cached_queue_cards = None
        self.simulator = simulator

    def get_crt_img(self):
        return self.board_img

    def get_hstate(self):
        if self._cached_hstate is None:
            self._simulate()
        return self._cached_hstate

    def _simulate(self):
        pool_cards, queue_cards = self.simulator.recognize(self.board_img)
        # update hstate
        if self._last_hstate is None:
            hstate = YangHiddenState.from_new_cards(pool_cards, queue_cards)
        else:
            hstate = self._last_hstate.continue_from_cards(pool_cards, queue_cards)
        self._cached_pool_cards = pool_cards
        self._cached_queue_cards = queue_cards
        self._cached_hstate = hstate

    def find_available_actions(self):
        if self._cached_pool_cards is None:
            print("Warning! Call find_available_actions before _simulate")
            self._simulate()

        return self._cached_pool_cards
    
    def get_action_prior_weights(self, actions):
        weights = []
        for action in actions:
            is_critical_action = action[7]
            if is_critical_action:
                weights.append(1)
            else:
                weights.append(0.01)
        return weights


class YangSimulatedState(YangBoardState):
    def __init__(self, board_img, last_hstate, simulator, *, pending_action):
        super().__init__(board_img, last_hstate, simulator)
        # self.board_img = board_img
        self.pending_action = pending_action
        # maybe root images and following actions?
        self._overlay_img = None
    
    def get_crt_img(self):
        # crt img is overlayed by the pending action
        if self._overlay_img is None:
            self._overlay_img = image_overlay(self.board_img, [self.pending_action])
        return self._overlay_img

    def _simulate(self):
        # override
        new_img = self.get_crt_img()
        pool_cards, queue_cards = self.simulator.recognize(new_img)
        queue_cards.append(self.pending_action) # add the pending action

        # update hstate
        if self._last_hstate is None:
            hstate = YangHiddenState.from_new_cards(pool_cards, queue_cards)
        else:
            hstate = self._last_hstate.continue_from_cards(pool_cards, queue_cards)
        self._cached_pool_cards = pool_cards
        self._cached_queue_cards = queue_cards
        self._cached_hstate = hstate
