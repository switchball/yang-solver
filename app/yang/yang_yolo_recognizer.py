import math
import numpy as np
import os
import random
import time
from PIL import Image
print("Loading YOLO ...")
from ultralytics import YOLO
print("YOLO loaded.")

from app.yang.yang_constants import (
    CARD_KINDS,
    MAIN_AREA_POSITION,
    VERBOSE, 
    CRITIC_AREA_CONFIG,
    # NUM_BOARD_ROWS,
    # NUM_BOARD_COLS,
    # SHOULD_SAVE_LOW_CONF_IMAGES,
)
from app.yang.logic.yang_board_state import YangBoardState

from controller.perceive.split_utils import split_image, crop_image
from controller.recognize.maybe_result import MaybeResult


class YangRecognizer:
    def __init__(self, model_path):
        self.yolo_recognizer = YangYOLORecognizer(model_path)
        self._last_hstate = None

    def recognize(self, full_image: Image) -> MaybeResult:
        crop_im = crop_image(full_image, MAIN_AREA_POSITION)
        state = YangBoardState(
            crop_im, 
            last_hstate=self._last_hstate, 
            simulator=self.yolo_recognizer
        )
        self._last_hstate = state.get_hstate() # this will call _simulate() which will call recognize
        hstate = state.get_hstate()  
        return MaybeResult(result=state, prob=1)


class YangYOLORecognizer:
    """借助YOLO模型识别棋盘的各个卡片位置"""
    def __init__(self, model_path):
        self.model = YOLO(model_path)
    
    def recognize(self, crop_im: Image):
        pool_cards = []
        queue_cards = []

        # crop_im = crop_image(full_image, MAIN_AREA_POSITION)
        width, height = crop_im.size

        result = self.model.predict(source=[crop_im], save=False, verbose=False, device="cuda:0")[0]
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()
            confidence = box.conf[0].item()
            class_id = box.cls[0].item()
            class_name = result.names[class_id]

            # 检测边界框需要是近似方的，i.e. 短边 / 长边 > 0.7 否则剔除
            range_x = x2 - x1
            range_y = y2 - y1
            if min(range_x, range_y) <= 0.7 * max(range_x, range_y):
                print(f"边界框不符合要求: range_x={range_x} range_y={range_y}")
                continue

            is_critical_action = self._calc_overlap_with_critic_area(x1, y1, x2, y2, width, height)
            if VERBOSE:
                print(f"类别: {class_name}, 置信度: {confidence:.2f}, 边界框: [{x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}], 是否关键: {is_critical_action}")

            # print(repr(confidence), type(confidence), type(x1), class_name)
            entry = (class_id, x1, y1, x2 - x1, y2 - y1, (x1 + x2) * .5, (y1 + y2) * .5, is_critical_action)

            # 检测边界框需要是近似方的，i.e. 短边 / 长边 > 0.7 
            range_x = x2 - x1
            range_y = y2 - y1
            if min(range_x, range_y) <= 0.7 * max(range_x, range_y):
                print(f"边界框不符合要求: range_x={range_x} range_y={range_y}")
                continue

            if entry[6] < 0.85 * height:
                pool_cards.append(entry)
            else:
                queue_cards.append(entry)
        return pool_cards, queue_cards
        # top_category = [result.probs.top1 for result in results]
        # top_confidence = [result.probs.top1conf for result in results]
        # recognize_result = np.array(top_category).reshape(rows, cols)
        # prod_confidence = math.prod(top_confidence)

        # self._save_low_conf_images(img_list, top_confidence)

        return recognize_result, prod_confidence

    def _calc_overlap_with_critic_area(self, x1, y1, x2, y2, width, height, overlap_threshold = 0.5) -> list:
        sum_area = sum(self._calc_overlap_with_critic_area_single(x1, y1, x2, y2, critic_area, (width, height)) for critic_area in CRITIC_AREA_CONFIG)
        # print("Sum Area:", sum_area, "Overlap Threshold:", overlap_threshold, "Overlap:", sum_area > overlap_threshold)
        return sum_area > overlap_threshold

    def _calc_overlap_with_critic_area_single(self, x1, y1, x2, y2, critic_area: list, image_size) -> list:
        """
        计算矩形 (x1, y1, x2, y2) 与 critic_area 的重叠面积占比。
        
        :param x1: 矩形左上角 x 坐标
        :param y1: 矩形左上角 y 坐标
        :param x2: 矩形右下角 x 坐标
        :param y2: 矩形右下角 y 坐标
        :param critic_area: tuple (x, y, w, h)，表示 critic area 的归一化坐标
        :param image_size: tuple (width, height)，表示图像的尺寸
        :return: 重叠面积占原矩形面积的比例 (0~1)
        """
        # 解包 critic_area 并还原为绝对坐标（假设图像尺寸为 width, height）
        img_w, img_h = image_size  # 如果是归一化坐标，可设为 1.0
        cx, cy, cw, ch = critic_area
        cx_abs = cx * img_w
        cy_abs = cy * img_h
        cw_abs = cw * img_w
        ch_abs = ch * img_h

        # 转换为左上右下坐标形式
        cx1, cy1 = cx_abs, cy_abs
        cx2, cy2 = cx_abs + cw_abs, cy_abs + ch_abs

        # 计算交集区域坐标
        inter_x1 = max(x1, cx1)
        inter_y1 = max(y1, cy1)
        inter_x2 = min(x2, cx2)
        inter_y2 = min(y2, cy2)

        # 如果没有交集
        if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
            return 0.0

        # 计算交集面积
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        # 原始矩形面积
        rect_area = (x2 - x1) * (y2 - y1)

        # 防止除以零
        if rect_area == 0:
            return 0.0

        # 返回重叠面积占比
        return inter_area / rect_area
