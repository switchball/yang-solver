import random
import time
from copy import deepcopy

def step(hstate):
    # print("in step, hstate=", hstate)
    qkeys_num = len(hstate["pool"])
    q = [0] * qkeys_num
    pool = hstate["pool"]
    empty_slot_num = hstate["queue_empty_slot"]

    # 尝试应用规则
    for chk_idx in range(qkeys_num):
        if hstate["pool"][chk_idx][1] >= 3:
            hstate["pool"][chk_idx][0] -= 3
            hstate["pool"][chk_idx][1] -= 3
            hstate["pool"][chk_idx][2] -= 3
            hstate["queue_empty_slot"] += 3
            hstate["score"] += 1
            print("Hited chk idx", chk_idx)
            if hstate["pool"][chk_idx][2] < 0:
                print("Fix1 negative left cards:", hstate)
                hstate["pool"][chk_idx][2] = 0
    empty_slot_num = hstate["queue_empty_slot"]

    if empty_slot_num == 0:
        return True  # no more moves
    for _idx in range(0, qkeys_num):
        # 若局面同类型数量出现 3
        if pool[_idx][0] >= 3:
            # 若 queue 已有 2,1,0 个
            if pool[_idx][1] == 2:
                q[_idx] = 901
            elif pool[_idx][1] == 1 and empty_slot_num >= 2:
                q[_idx] = 802
            elif pool[_idx][1] == 0 and empty_slot_num >= 3:
                q[_idx] = 703
        # 若局面同类型数量出现 2
        elif pool[_idx][0] == 2:
            # 若 queue 已有 1,0 个
            if pool[_idx][1] == 1:
                q[_idx] = 601
            elif pool[_idx][1] == 0:
                q[_idx] = 501
        # 若局面同类型数量出现 1
        elif pool[_idx][0] == 1:
            # 仅 queue 为 0 可移动
            if pool[_idx][1] == 0:
                q[_idx] = 101

    # 选择 q 值最大的进行移动
    max_q = max(q)
    # print(q, max_q, 'q max q')
    if max_q == 0:
        return True  # terminal state
    
    argmax_idx = [idx for idx, v in enumerate(q) if v == max_q]
    op_idx = random.choice(argmax_idx)
    # print(f"q={q} selected operation idx={op_idx}")

    # 展示移动(原地修改)
    hstate["pool"][op_idx][1] += 1
    hstate["queue_empty_slot"] -= 1

    # 尝试消除(原地修改)
    hstate["pool_available_choice"] -= 1
    if hstate["pool"][op_idx][1] == 3:
        hstate["pool"][op_idx][0] -= 3
        hstate["pool"][op_idx][1] = 0
        hstate["pool"][op_idx][2] -= 3
        hstate["queue_empty_slot"] += 3
        hstate["score"] += 1
        # print("clear pool for op_idx =", op_idx)
        # 修正负数剩余牌
        if hstate["pool"][op_idx][2] < 0:
            print("Fix2 negative left cards:", hstate)
            hstate["pool"][op_idx][2] = 0


    # 对 pool 进行概率盲盒
    pick_cnt = 1 if random.random() < 0.5 else 0
    if hstate["pool_available_choice"] == 0:
        pick_cnt = 1
    elif hstate["pool_available_choice"] < 8:
        pick_cnt = random.randint(0, 2)

    # 开盲盒加牌(原地修改)
    for _ in range(pick_cnt):
        # 根据剩余牌数确定概率
        weights = [v[2] for v in pool.values()]
        if sum(weights) == 0:
            # print("No card to pick")
            continue
        pick_idx = random.choices(list(pool.keys()), weights=weights, k=1)[0]

        # 翻出牌(原地修改)
        # print("random pick idx =", pick_idx, "with probility", pool[pick_idx][2]/sum(weights), "and pool available choice =", hstate["pool_available_choice"])
        pool[pick_idx][0] += 1
        pool[pick_idx][2] -= 1
        hstate["pool_available_choice"] += 1


    return False

def loop_for_rewards(init_hstate, loop_num=100):
    hstate_dict = init_hstate._hstate
    total_score = 0
    tic = time.time_ns() / 1000000
    for k in range(loop_num):
        hstate = deepcopy(hstate_dict)
        while not (is_terminal := step(hstate)):
            pass
            # print(".", end="")

        # print("W" if hstate["queue_empty_slot"] == 7 else "L", f"Score: {hstate['score']}")
        total_score += hstate["score"]
        toc = time.time_ns() / 1000000
    
    max_score = sum([y[0] + y[2] for y in hstate_dict["pool"].values()]) / 3

    print(f"Mean Score: {total_score/loop_num} Max: {max_score} Score%: {total_score/loop_num/max_score}")
    print(f"Time: {(toc-tic) / 100} ms")
    return total_score / loop_num

if __name__ == "__main__":
    state = (
        {"p1": 1, "p2": 1, "p3": 2, "p4": 2},
        [3, 4, 0, 0, 0, 0, 0]
    )

    total_score = 0
    tic = time.time_ns() / 1000000
    for k in range(1):
        hstate = {
            # type: [total_num, total_queue_num, uncover_num]
            "pool": {
                0: [0, 0, 3],
                1: [2, 0, 4],
                2: [2, 0, 4],
                3: [1, 1, 5],
                4: [1, 1, 5],
                5: [0, 0, 6],
                6: [0, 0, 6],
                7: [0, 0, 6],
                8: [0, 0, 6],
                9: [0, 0, 15],
                10: [0, 0, 9],
                11: [0, 0, 9],
                12: [0, 0, 9],
            },
            # "queue": [3, 4, 0, 0, 0, 0, 0],
            "pool_available_choice": 4,
            "queue_empty_slot": 5, 
            "score": 0,
        }

        hstate = {'pool': {0: [0, 0, 18], 1: [1, 0, 17], 2: [3, 0, 15], 3: [3, 1, 15], 4: [1, 1, 17], 5: [4, 0, 14], 6: [4, 1, 14], 7: [3, 1, 15], 8: [0, 0, 18], 9: [2, 0, 16], 10: [2, 0, 16], 11: [1, 1, 17], 12: [1, 0, 17], 13: [2, 1, 16], 14: [2, 0, 16], 15: [0, 0, 18]}, 'pool_available_choice': 23, 'queue_empty_slot': 1, 'score': 0}
        hstate = {'pool': {0: [0, 0, 18], 1: [1, 0, 17], 2: [3, 0, 15], 3: [4, 1, 14], 4: [1, 1, 17], 5: [3, 0, 15], 6: [4, 2, 14], 7: [3, 1, 15], 8: [0, 0, 18], 9: [2, 0, 16], 10: [2, 0, 16], 11: [1, 0, 17], 12: [1, 0, 17], 13: [2, 1, 16], 14: [2, 0, 16], 15: [0, 0, 18]}, 'pool_available_choice': 23, 'queue_empty_slot': 1, 'score': 0}

        while not (is_terminal := step(hstate)):
            # pass
            print(is_terminal, hstate)
            print(".", end="")

        print("W" if hstate["queue_empty_slot"] == 7 else "L", f"Score: {hstate['score']}")
        total_score += hstate["score"]
    
    toc = time.time_ns() / 1000000
    print(f"Mean Score: {total_score/1000} {total_score/1000/30}")
    print(f"Time: {(toc-tic) / 100} ms")
    

    # for j in range(30):
    #     is_terminal = step(hstate)
    #     print()
    #     print(f"#{j}\tNow hstate:", hstate)
    #     print("-"*20)
    #     if is_terminal:
    #         print("No more operation!")
    #         if hstate["queue_empty_slot"] == 7:
    #             print("You win!")
    #         else:
    #             print("You lose!")
    #         break
