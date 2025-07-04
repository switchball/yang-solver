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
            print(f"类别: {class_name}, 置信度: {confidence:.2f}, 边界框: [{x1}, {y1}, {x2}, {y2}]")
            # print(repr(confidence), type(confidence), type(x1), class_name)
            entry = (class_id, x1, y1, x2 - x1, y2 - y1, (x1 + x2) * .5, (y1 + y2) * .5)

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
