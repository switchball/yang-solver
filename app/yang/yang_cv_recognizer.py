import cv2
import numpy as np
from PIL import Image, ImageGrab
from skimage.metrics import structural_similarity

from app.yang.yang_constants import MAIN_AREA_POSITION, CARD_KINDS
from app.yang.yang_hstate import YangHiddenState

from controller.perceive.split_utils import crop_image
from controller.recognize.base_recognizer import BaseRecognizer
from controller.recognize.maybe_result import MaybeResult


class YangCvRecognizer(BaseRecognizer):
    def __init__(self):
        super().__init__()
        self._last_img = None
        self._last_hstate = None

    def recognize(self, image: Image) -> MaybeResult:
        # self._last_img = image
        crop_im = crop_image(image, MAIN_AREA_POSITION)

        pool_cards, queue_cards = self.get_cards(np.array(crop_im), normalize=False)
        print("P\n", np.array(pool_cards), "\nQ\n", np.array(queue_cards), '#')

        if self._last_hstate is None:
            hstate = YangHiddenState.from_new_cards(pool_cards, queue_cards, pending_actions=[])
        else:
            hstate = self._last_hstate.continue_from_cards(pool_cards, queue_cards)

        self._last_hstate = hstate

        return MaybeResult(result=hstate, prob=1)

    def get_cards(self, im: np.array, normalize=False, pool_queue_split_ratio=0.85, min_area=5000):
        """
        使用 CV 方法识别卡牌
        :param im: np.array 待识别的图片
        :param normalize: bool 返回的坐标值是否归一化
        :param pool_queue_split_ratio: float 池子与待消除序列的在 y 轴的分割比例
        :param min_area: int 卡牌最小面积过滤阈值
        :return: (list[list], list[list]) 池子中的卡牌, 待消除序列中的卡牌
                    每一行包含: label, x, y, w, h, center_x, center_y
        """
        pool_cards = []  # 池子中的卡牌
        queue_cards = []  # 待消除序列中的卡牌
        flag = np.mean(np.abs(im - np.array([245,255,205])), 2) < 15  # 获取卡牌背景
        flag = np.array(flag, dtype='uint8')

        imgs = np.zeros((16,45,45,3), dtype='uint8')  # 读取标注模板
        for i in range(CARD_KINDS):
            imgs[i] = np.array(Image.open(f'images/cards/{i}.png'))

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(flag, connectivity=8)

        for i in range(num_labels):
            if stats[i,4] > 500 and i != 0:  # 判定为卡牌
                x, y, w, h = stats[i,:4]
                center_x,center_y = centroids[i]

                img = im[y:y+h,x:x+w]  # 将判定为卡牌的区域单独取出来作为img
                img = np.array(Image.fromarray(img).resize((45, 45)))

                ssmi = np.zeros(16)
                for j in range(16):  # 将img和标签逐个比较
                    ssmi[j] = structural_similarity(img, imgs[j], data_range=255, channel_axis=2)
                label = np.argmax(ssmi)

                entry = [label, x, y, w, h, int(center_x), int(center_y)]
                area = w * h
                if area < min_area:  # 卡牌面积太小则忽略
                    continue
                height, width = im.shape[:2]  # 注意数组情况下的 shape 是反过来的
                if normalize:
                    entry = [label, x/width, y/height, w/width, h/height, center_x/width, center_y/height]

                if int(center_y) < pool_queue_split_ratio * height:
                    pool_cards.append(entry)  # 池子中的卡牌
                else:  
                    queue_cards.append(entry)  # 待消除序列中的卡牌

        pool_cards = np.array(pool_cards).tolist()
        queue_cards = np.array(queue_cards).tolist()

        return pool_cards, queue_cards
