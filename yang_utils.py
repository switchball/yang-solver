import cv2
import numpy as np
from PIL import Image, ImageGrab
from skimage.metrics import structural_similarity

def getcards(im):
    #返回一个numpy数组，每一行包含：label,x,y,w,h,center_x,center_y
    cards = []
    flag = np.mean(np.abs(im - np.array([245,255,205])), 2) < 15  #获取卡牌背景
    flag = np.array(flag, dtype='uint8')

    imgs = np.zeros((16,45,45,3), dtype='uint8')  #读取标注模板
    for i in range(16):
        imgs[i] = np.array(Image.open(f'images/cards/{i}.png'))

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(flag, connectivity=8)

    for i in range(num_labels):
        if stats[i,4] > 500 and i != 0:  #判定为卡牌
            x,y,w,h = stats[i,:4]
            center_x,center_y = centroids[i]

            img = im[y:y+h,x:x+w]  #将判定为卡牌的区域单独取出来作为img
            img = np.array(Image.fromarray(img).resize((45,45)))

            ssmi = np.zeros(16)
            for j in range(16):  #将img和标签逐个比较
                ssmi[j] = structural_similarity(img, imgs[j], win_size=7, data_range=255, channel_axis=2)
            label = np.argmax(ssmi)

            cards.append([label,x,y,w,h,int(center_x),int(center_y)])  #存放如cards

    cards = np.array(cards)
    return cards

if __name__ == '__main__':
    XYWHN = (0.05, 0.19, 0.9, 0.68)
    from controller.perceive.split_utils import crop_image
    # im = from screenshot1.png
    im = Image.open('screenshot2.png')

    crop_im = crop_image(im, xywhn=XYWHN)
    crop_im.save('crop_im2.png')
    print(crop_im.size)
    cards = getcards(np.array(crop_im))
    print(cards)
    width, height = crop_im.size
    with open("crop_im2.txt", "w") as f:
        for card in cards:
            buffer = f"{card[0]} {card[5]/width:.6f} {card[6]/height:.6f} {card[3]/width:.6f} {card[4]/height:.6f}"
            f.write(buffer + "\n")
