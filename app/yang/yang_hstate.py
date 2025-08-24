from __future__ import annotations
from collections import Counter

from app.yang.yang_constants import CARD_KINDS, RWD_NON_CRITICAL_ACTION, RWD_IS_CRITICAL_ACTION

class YangHiddenState:
    INIT_CARDS = 5 * 3  # each 5 copy(s)

    def __init__(self, hstate: dict):
        self._hstate = hstate
    
    @property
    def available_choice_num(self):
        return self._hstate["pool_available_choice"]

    @property
    def remaining_slot_num(self):
        return self._hstate["queue_empty_slot"]
    
    @property
    def score(self):
        return self._hstate["score"]

    def get_each_uncovered_cards(self):
        """
        返回每个种类的未翻牌数
        """
        pool = self._hstate["pool"]
        return [pool[k][2] for k in range(CARD_KINDS)]

    def get_each_remaining_cards(self):
        """
        返回每个种类的剩余牌数 + 场上存在牌数
        """
        pool = self._hstate["pool"]
        return [pool[k][0] + pool[k][2] for k in range(CARD_KINDS)]
    
    def get_each_in_queue_cards(self):
        """
        返回每个种类的在队列中的牌数
        """
        pool = self._hstate["pool"]
        return [pool[k][1] for k in range(CARD_KINDS)]

    @classmethod
    def from_new_cards(cls, pool_cards: list, queue_cards: list, pending_actions, old_score=0, each_uncovered_cards=None):
        """
        从全新局面创建 HState, 或者继承分数和剩余牌数
        """
        if each_uncovered_cards is None:
            each_uncovered_cards = [cls.INIT_CARDS for k in range(CARD_KINDS)]
        queue_cards.extend(pending_actions)
        cnt = Counter([c[0] for c in pool_cards + queue_cards])
        pool = {}
        # all cards
        for k in range(CARD_KINDS):
            card_uncovered_num = each_uncovered_cards[k]
            if k in cnt:
                pool[k] = [cnt[k], 0, card_uncovered_num]
            else:
                pool[k] = [0, 0, card_uncovered_num]
        reduced_num = 0
        for c in queue_cards:
            pool[c[0]][1] += 1
            # queue 中的三消
            while pool[c[0]][1] >= 3:
                pool[c[0]][0] -= 3
                pool[c[0]][1] -= 3
                pool[c[0]][2] -= 3
                reduced_num += 3
                print("!! 三消 ", c[0])

        # action score
        action_rwd = 0
        for action in pending_actions:
            is_critical_action = action[7]
            action_rwd += RWD_NON_CRITICAL_ACTION if not is_critical_action else RWD_IS_CRITICAL_ACTION

        empty_slot_num = 7 - len(queue_cards) + reduced_num
        hstate = {
            "pool": pool,
            "pool_available_choice": len(pool_cards),
            "queue_empty_slot": empty_slot_num, 
            "score": reduced_num + old_score + action_rwd,
        }

        return cls(hstate)

    def continue_from_cards(self, pool_cards, queue_cards, pending_actions) -> YangHiddenState:
        """
        从一个已有的局面创建 HState, 继承分数和剩余牌数
        """
        each_reamining_num = self.get_each_remaining_cards()
        each_in_queue_num = self.get_each_in_queue_cards()
        prior_hstate = YangHiddenState.from_new_cards(pool_cards, queue_cards, pending_actions)

        empty_slot_num = prior_hstate.remaining_slot_num
        
        if self.remaining_slot_num == empty_slot_num:
            return self
        
        if self.remaining_slot_num > empty_slot_num:
            # 可用格子数减少了，认为没有消除
            each_reamining_num = self.get_each_remaining_cards()

            cnt_all = Counter([c[0] for c in pool_cards + queue_cards])
            cnt_queue = Counter([c[0] for c in queue_cards])
            pool = {}
            for k in range(CARD_KINDS):
                appear_num = cnt_all.get(k, 0)
                in_queue_num = cnt_queue.get(k, 0)
                pool[k] = [
                    appear_num,
                    in_queue_num,
                    each_reamining_num[k] - appear_num,
                ]
            hstate = {
                "pool": pool,
                "pool_available_choice": len(pool_cards),
                "queue_empty_slot": empty_slot_num, 
                "score": self.score,
            }
            return YangHiddenState(hstate)
        
        if self.remaining_slot_num < empty_slot_num:
            # 可用格子数增加了，认为消除了
            each_reamining_num = self.get_each_remaining_cards()
            each_in_queue_num = self.get_each_in_queue_cards()

            cnt_all = Counter([c[0] for c in pool_cards + queue_cards])
            cnt_queue = Counter([c[0] for c in queue_cards])
            pool = {}
            for k in range(CARD_KINDS):
                appear_num = cnt_all.get(k, 0)
                in_queue_num = cnt_queue.get(k, 0)
                if in_queue_num < each_in_queue_num[k]:
                    each_reamining_num[k] -= 3  # 这时 3 张牌消除
                pool[k] = [
                    appear_num,
                    in_queue_num,
                    each_reamining_num[k] - appear_num,
                ]
            hstate = {
                "pool": pool,
                "pool_available_choice": len(pool_cards),
                "queue_empty_slot": empty_slot_num, 
                "score": self.score + 1,
            }
            return YangHiddenState(hstate)