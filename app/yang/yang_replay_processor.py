import numpy as np
import random
import threading

from PIL import Image, ImageDraw

from app.yang.yang_cv_recognizer import YangCvRecognizer
from app.yang.yang_constants import MAIN_AREA_POSITION

from controller.perceive.split_utils import crop_image


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
            dict_of_images_and_labels = self.process_traj(traj)

            for ovs_idx, images_and_labels in dict_of_images_and_labels.items():
                # folder structure is like yolo
                for idx, (image, label) in enumerate(zip(*images_and_labels)):
                    train_or_val = "train" if random.random() < train_val_ratio else "val"
                    image_folder = os.path.join(save_folder, "images", train_or_val)
                    label_folder = os.path.join(save_folder, "labels", train_or_val)
                    if not os.path.exists(image_folder):
                        os.makedirs(image_folder)
                    if not os.path.exists(label_folder):
                        os.makedirs(label_folder)

                    filename = f"{traj_dir}_{ovs_idx:02d}_{idx:04d}"
                    image.save(os.path.join(image_folder, filename + ".png"))
                    with open(os.path.join(label_folder, filename + ".txt"), "w") as f:
                        f.write(label)
                    self.logger.info("Saved image {} to {}".format(filename, image_folder))
                    self.logger.info("Saved label {} to {}".format(filename, label_folder))
            # break

    def load_trajectory(self, traj_folder):
        # the trajectory is a list of images and a list of actions
        # images is named as 0000.png, 0001.png, ...
        # actions is all contained in actions.txt
        images = []
        actions = []
        for filename in sorted(os.listdir(traj_folder)):
            if filename.endswith(".png"):
                # crop Image object via MAIN_AREA_POSITION
                img = Image.open(os.path.join(traj_folder, filename))
                crop_im = crop_image(img, MAIN_AREA_POSITION)
                images.append(crop_im)
            elif filename.endswith(".txt"):
                actions = self.load_actions(os.path.join(traj_folder, filename))
            else:
                raise ValueError("Unknown filetype: {}".format(image_name))
        
        self.logger.info("Loaded trajectory {} with {} images and {} actions".format(traj_folder, len(images), len(actions)))
        return images, actions


    def load_actions(self, actions_file):
        """读入 actions.txt 返回相对窗口左上角的动作坐标
        再根据 MAIN_AREA_POSITION 做子集
        """
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
                act_x, act_y = action[0] - left, action[1] - top
                # transform via MAIN_AREA_POSITION
                main_x, main_y, main_w, main_h = MAIN_AREA_POSITION

                # MAIN AREA 左上角的坐标
                rect_x = width * main_x
                rect_y = height * main_y

                actions.append((act_x - rect_x, act_y - rect_y))
                # actions.append((action[0] - left, action[1] - top))

        return actions

    def process_traj(self, traj):
        images, actions = traj
        self.logger.info("Processing trajectory with {} images and {} actions".format(len(images), len(actions)))
        labels = []
        active_pool_cards = []
        active_queue_cards = []
        selected_cards = []
        # mark available actions by cv method
        idx = 0
        for step_img, step_act in zip(images, actions):
            pool_cards, queue_cards = self.cv_recognizer.get_cards(np.array(step_img), normalize=False, pool_queue_split_ratio=0.85)
            print("image idx", idx, "#pool cards:", len(pool_cards), "#queue cards:", len(queue_cards))
            # print("pool cards", pool_cards)
            # print("queue cards", queue_cards)
            assert len(queue_cards) <= 7, "Queue cards should be less than 7"
            # get the action's label
            label, selected_card = self.get_action_label_in_pool(step_act, pool_cards)
            selected_cards.append(selected_card)
        
            width, height = step_img.size
            label_buffer = ""
            for card in pool_cards + queue_cards:
                buffer = f"{card[0]} {card[5]/width:.6f} {card[6]/height:.6f} {card[3]/width:.6f} {card[4]/height:.6f}"
                # print(buffer)
                label_buffer += buffer + "\n"
                area = card[3] * card[4]
                # if area < 5000:
                #     print(f"Area: {area} ( = {card[3]} * {card[4]}")
            active_pool_cards.append(pool_cards)
            active_queue_cards.append(queue_cards)
            labels.append(label_buffer)
            idx += 1
        
        self.logger.info(f"Directly Processed trajectory with output {len(labels)} labels")
        num_pair = len(labels)

        # do state-action overshoot
        overshoot_max = min(7, num_pair - 1)
        ovs_images = {k + 1: [] for k in range(overshoot_max)}
        ovs_labels = {k + 1: [] for k in range(overshoot_max)}
        for i in range(num_pair - 1): # range(num_pair - overshoot_max):
            img_i = images[i]
            for k in range(overshoot_max):
                # print(f"Overshoot {i=} + {k=} ? {num_pair=} => {i+k+1<num_pair}")
                if i + k + 1 >= num_pair:
                    break
                # s[i] + act[i:i+k] => s[k+1]
                # get the label of selected_card of the next k actions
                # selected_cards: array of (label, x, y, w, h, center_x, center_y)
                new_img = self.image_overlay(img_i, selected_cards[i:i+k+1])
                ovs_images[k+1].append(new_img)
                # new_img.save("tmp.png")
                width, height = new_img.size
                label_buffer = ""
                for pcard in active_pool_cards[i+k+1]:
                    # 如果 labels 的4个角位，都被 masks 覆盖，则将其类型修改为 undefiend
                    covered = self.is_single_card_be_covered_by_cards(pcard, selected_cards[i:i+k+1])
                    _label = 15 if covered else pcard[0]
                    buffer = f"{_label} {pcard[5]/width:.6f} {pcard[6]/height:.6f} {pcard[3]/width:.6f} {pcard[4]/height:.6f}"
                    label_buffer += buffer + "\n"
                    # print(f"{pcard=} {covered=}")
                for qcard in active_queue_cards[i]:
                    buffer = f"{qcard[0]} {qcard[5]/width:.6f} {qcard[6]/height:.6f} {qcard[3]/width:.6f} {qcard[4]/height:.6f}"
                    label_buffer += buffer + "\n"

                ovs_labels[k+1].append(label_buffer)

        ret = {0: (images, labels)}
        for k in range(overshoot_max):
            ret[k+1] = (ovs_images[k+1], ovs_labels[k+1])
        return ret
            

    def get_action_label_in_pool(self, action, pool_cards):
        """检查某个点击动作，是否在pool的cards坐标中"""
        for card in pool_cards:
            label, x, y, w, h, center_x, center_y = card
            if x <= action[0] <= x + w and y <= action[1] <= y + h:
                return label, tuple(card)
        self.logger.info("Invalid action: {} pool_cards: {} try loose pixels = 5".format(action, pool_cards))
        for card in pool_cards:
            label, x, y, w, h, center_x, center_y = card
            if x - 5 <= action[0] <= x + w + 5 and y - 5 <= action[1] <= y + h + 5:
                return label, tuple(card)
        assert False, "Invalid action: {} pool_cards: {}".format(action, pool_cards)

    def image_overlay(self, img_i, selected_cards):
        """
        Overlay black circles on the original image at specified positions.

        Parameters:
        img_i (PIL.Image): The original image.
        selected_cards (list of tuples): A list of tuples where each tuple contains
                                        (label, x, y, w, h, center_x, center_y).

        Returns:
        PIL.Image: A new image with black circles overlaid.
        """
        # Create a copy of the original image
        new_img = img_i.copy()
        draw = ImageDraw.Draw(new_img)

        for card in selected_cards:
            _, _, _, w, _, center_x, center_y = card
            radius = w / 3
            # Calculate the bounding box for the circle
            left_up_point = (center_x - radius, center_y - radius)
            right_down_point = (center_x + radius, center_y + radius)
            # Draw the black circle
            draw.ellipse([left_up_point, right_down_point], fill='black')

        return new_img
 
    def is_single_card_be_covered_by_cards(self, pcard, selected_cards):
        """
        Check if the four quarter centers of pcard are covered by the union of rectangles of selected_cards.

        Parameters:
        pcard (tuple): The card to check, containing (label, x, y, w, h, center_x, center_y).
        selected_cards (list of tuples): List of cards, each containing (label, x, y, w, h, center_x, center_y).

        Returns:
        bool: True if all four quarter centers of pcard are covered by the union of rectangles, False otherwise.
        """
        x, y, w, h = pcard[1], pcard[2], pcard[3], pcard[4]
        
        # Calculate the four quarter centers
        quarter_centers = [
            (x + w / 4, y + h / 4),    # Top-left quarter center
            (x + 3 * w / 4, y + h / 4), # Top-right quarter center
            (x + w / 4, y + 3 * h / 4), # Bottom-left quarter center
            (x + 3 * w / 4, y + 3 * h / 4) # Bottom-right quarter center
        ]

        # Check if all four quarter centers are covered
        for center_x, center_y in quarter_centers:
            if not self.is_point_covered_by_cards(center_x, center_y, selected_cards):
                return False

        return True

    def is_point_covered_by_cards(self, center_x, center_y, selected_cards):
        """
        Check if a given point is covered by any of the rectangles in selected_cards.

        Parameters:
        center_x (float): The x-coordinate of the point.
        center_y (float): The y-coordinate of the point.
        selected_cards (list of tuples): List of cards, each containing (label, x, y, w, h, center_x, center_y).

        Returns:
        bool: True if the point is covered by any rectangle, False otherwise.
        """
        for card in selected_cards:
            x, y, w, h = card[1], card[2], card[3], card[4]
            left = x
            right = x + w
            top = y
            bottom = y + h

            if left <= center_x <= right and top <= center_y <= bottom:
                return True

        return False

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
    p.load_process_replays(args.replay_folder, save_folder="datasets/yang_v3")