import os
import time
import random
import logging
import threading

from controller.collect.collect_utils import MouseKeyboardListener
from controller.perceive.window_utils import capture_window
from controller.recognize.base_recognizer import BaseRecognizer
from controller.react.base_react import BaseReact
from controller.log_config import setup_logging


class YangListener(MouseKeyboardListener):
    def __init__(self, queue, hotkey="Q", verbose=False):
        super().__init__(hotkey, verbose)
        self.logger = logging.getLogger(__name__)
        self.click_action_queue = queue

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.click_action_queue.append((x, y))
            self.logger.info(f"Clicked at ({x},{y})")


class YangRecorder(object):
    def __init__(self, config: dict):
        self.logger = logging.getLogger(__name__)
        self.window_title = config["window_title"]
        self.recognizer : BaseRecognizer = config["recognizer"]
        self.react : BaseReact = config["react"]

        self.frame_seconds = 1 / config["fps"]
        self.frame_max_running = config["frame_max_running"]

        self.img_state_list = []  # 图片的状态序列
        self.action_list = []     # 执行的动作序列

        self.click_action_queue = []  # 监听的点击动作队列
        self.cached_coords = (0, 0, 0, 0)
        self.listener = YangListener(self.click_action_queue, hotkey="Q", verbose=False)

    @property
    def should_wait_img(self):
        """是否等待图像输入(True) 否则为等待动作输入(False)"""
        return len(self.img_state_list) <= len(self.action_list)

    def _capture(self):
        try:
            # perceive
            coords, screenshot = capture_window(self.window_title)
            return coords, screenshot
        except Exception as e:
            self.logger.error(f"捕获窗口失败: {e}")
            return None, None

    def main_record_loop(self):
        thread = threading.Thread(target=self.listener.start_listening)
        thread.daemon = True
        thread.start()
        crt_coords = None
        tic = time.time()
        while (tic + 10) > time.time():
            if self.should_wait_img:
                # 等待截图
                coords, screenshot = self._capture()
                if screenshot is None:
                    continue
                crt_coords = coords
                self.cached_coords = crt_coords
                self.img_state_list.append(screenshot)
                self.logger.info("得到截图")
                if len(self.click_action_queue) > 0:
                    self.logger.info(f"点击队列已清空 ({len(self.click_action_queue)})")
                    self.click_action_queue.clear()
            else:
                # 等待动作
                if len(self.click_action_queue) > 0:
                    crt_action = self.click_action_queue.pop(0)
                    click_x, click_y = crt_action
                    # 判断动作是否有效
                    # crt_coords: (left, top, width, height)
                    if coords[0] <= click_x <= coords[0] + coords[2] and coords[1] <= click_y <= coords[1] + coords[3]:
                        self.action_list.append(crt_action)
                        self.logger.info("得到动作, 等待 0.4 秒 ...")
                        time.sleep(0.4)
                    else:
                        self.logger.info(f"Out of bounds because click_point ({click_x}, {click_y}) is out of bounds")
                else:
                    time.sleep(0.01)  # 留空
        
        self.save_records()

    def save_records(self):
        folder_path = "replays"
        self.logger.info(f"准备保存操作记录到 {folder_path}")
        # if not os.path.exists(folder_path):
        #     os.makedirs(folder_path)
        # sub folder named with traj_day + hhmmss
        sub_folder_path = os.path.join(folder_path, f"traj_{time.strftime('%Y%m%d_%H%M%S', time.localtime())}")
        os.makedirs(sub_folder_path)
        for i, img in enumerate(self.img_state_list):
            img_path = os.path.join(sub_folder_path, f"{i:04d}.png")
            img.save(img_path)
        self.logger.info(f"已保存 {len(self.img_state_list)} 张图片到文件到 {sub_folder_path}")


        with open(os.path.join(sub_folder_path, f"actions.txt"), "w") as f:
            # write coords
            c = self.cached_coords
            f.write(f"{c[0]},{c[1]},{c[2]},{c[3]}\n")
            for act in self.action_list:
                f.write(f"{act[0]},{act[1]}\n")
        self.logger.info(f"已保存 {len(self.action_list)} 个动作到文件到 {sub_folder_path}")

    def main_loop(self):
        tic = time.time()
        next_tick = tic + self.frame_seconds

        crt_frame = 0

        while crt_frame < self.frame_max_running:
            crt_frame += 1
            if (toc := time.time()) < next_tick:
                time.sleep((next_tick - toc) * random.random())
            next_tick = time.time() + self.frame_seconds
            print(f"\n{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

            # capture
            coords, screenshot = self._capture()

            # recognize
            maybe_result = self.recognizer.recognize(screenshot)

            # react
            # gui_action = self.react.react(maybe_result)

            # # execute
            # gui_action.execute(coords)
        
        print("Main Loop End")


if __name__ == "__main__":
    setup_logging(log_file="logs/record.log")
    logger = logging.getLogger(__name__)
    logger.info("Starting recorder")

    recorder = YangRecorder({
        "window_title": "Code",
        "recognizer": None,
        "react": None,
        "fps": 1,
        "frame_max_running": 1000,
    })
    recorder.main_record_loop()