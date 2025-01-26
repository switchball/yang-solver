import numpy as np
import random
import threading

from PIL import Image

from app.yang.yang_cv_recognizer import YangCvRecognizer


class YangReplayProcessor(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cv_recognizer = YangCvRecognizer()
        random.seed(42)

    def load_process_replays(self, replay_folder="replays", save_folder="datasets/yang_v1", train_val_ratio=0.8):
        # for each replay in the folder, load the trajectory
        self.logger.info("Loading replays from {}".format(replay_folder))
        print()
        for traj_dir in os.listdir(replay_folder):
            traj_sub_dir = os.path.join(replay_folder, traj_dir)
            # traj sub dir contains 0000.png, 0001.png, ...
            traj = self.load_trajectory(traj_sub_dir)
            images_and_labels = self.process_traj(traj)

            # folder structure is like yolo
            for idx, (image, label) in enumerate(zip(*images_and_labels)):
                train_or_val = "train" if random.random() < train_val_ratio else "val"
                image_folder = os.path.join(save_folder, "images", train_or_val)
                label_folder = os.path.join(save_folder, "labels", train_or_val)
                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)
                if not os.path.exists(label_folder):
                    os.makedirs(label_folder)

                filename = f"{traj_dir}_{idx:06d}"
                image.save(os.path.join(image_folder, filename + ".png"))
                with open(os.path.join(label_folder, filename + ".txt"), "w") as f:
                    f.write(label)
                self.logger.info("Saved image {} to {}".format(filename, image_folder))
                self.logger.info("Saved label {} to {}".format(filename, label_folder))

    def load_trajectory(self, traj_folder):
        # the trajectory is a list of images and a list of actions
        # images is named as 0000.png, 0001.png, ...
        # actions is all contained in actions.txt
        images = []
        actions = []
        for filename in sorted(os.listdir(traj_folder)):
            if filename.endswith(".png"):
                # append Image object
                images.append(Image.open(os.path.join(traj_folder, filename)))
            elif filename.endswith(".txt"):
                actions = self.load_actions(os.path.join(traj_folder, filename))
            else:
                raise ValueError("Unknown filetype: {}".format(image_name))
        
        self.logger.info("Loaded trajectory {} with {} images and {} actions".format(traj_folder, len(images), len(actions)))
        return images, actions


    def load_actions(self, actions_file):
        """读入 actions.txt 返回相对窗口左上角的动作坐标"""
        # the first line is the (x, y, w, h) of where the image is like
        # the next lines is the clicked absolute position of the mouse
        # example:
        coords = None
        actions = []

        with open(actions_file, "r") as f:
            # read first line
            coords = f.readline().strip().split(",")
            coords = [int(c) for c in coords]
            left, top, width, height = coords
            # read next lines
            for line in f:
                action = line.strip().split(",")
                action = [int(a) for a in action]
                actions.append((action[0] - left, action[1] - top))

        return actions

    def process_traj(self, traj):
        images, actions = traj
        self.logger.info("Processing trajectory with {} images and {} actions".format(len(images), len(actions)))
        labels = []
        # mark available actions by cv method
        idx = 0
        for step_img, step_act in zip(images, actions):
            pool_cards, queue_cards = self.cv_recognizer.get_cards(np.array(step_img), normalize=False, pool_queue_split_ratio=0.8)
            print("image idx", idx)
            print("pool cards", pool_cards)
            print("queue cards", queue_cards)
            assert len(queue_cards) <= 7, "Queue cards should be less than 7"
            # get the action's label
            label = self.get_action_label_in_pool(step_act, pool_cards)
        
            width, height = step_img.size
            label_buffer = ""
            for card in pool_cards + queue_cards:
                buffer = f"{card[0]} {card[5]/width:.6f} {card[6]/height:.6f} {card[3]/width:.6f} {card[4]/height:.6f}"
                # print(buffer)
                label_buffer += buffer + "\n"
                area = card[3] * card[4]
                # if area < 5000:
                #     print(f"Area: {area} ( = {card[3]} * {card[4]}")
            labels.append(label_buffer)
            print('='*55)
            idx += 1
        
        self.logger.info(f"Processed trajectory with output {len(labels)} labels")
        return images, labels
            

    def get_action_label_in_pool(self, action, pool_cards):
        """检查某个点击动作，是否在pool的cards坐标中"""
        for card in pool_cards:
            label, x, y, w, h, center_x, center_y = card
            if x <= action[0] <= x + w and y <= action[1] <= y + h:
                return label
        self.logger.info("Invalid action: {} pool_cards: {} try loose pixels = 5".format(action, pool_cards))
        for card in pool_cards:
            label, x, y, w, h, center_x, center_y = card
            if x - 5 <= action[0] <= x + w + 5 and y - 5 <= action[1] <= y + h + 5:
                return label
        assert False, "Invalid action: {} pool_cards: {}".format(action, pool_cards)


if __name__ == "__main__":
    import os
    import sys
    import logging
    import argparse

    from controller.log_config import setup_logging

    setup_logging("logs/replay_processor.log")

    parser = argparse.ArgumentParser(description="Process replay files")
    parser.add_argument("--replay_folder", type=str, default="replays", help="The folder containing the replay files")
    args = parser.parse_args()

    p = YangReplayProcessor()
    p.load_process_replays(args.replay_folder)