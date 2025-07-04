from PIL import Image, ImageDraw, ImageFont
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

def image_overlay(img_i, selected_cards):
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


def image_bbox_overlay(
    img_i, 
    selected_cards,
    border_width=3,         # 新增边框粗细参数，默认3像素
    font_size=14,           # 新增字体大小参数，默认14px
    font_path=None          # 新增可选字体路径参数
):
    """
    在图像上绘制带标签的边界框（支持高分辨率适配）
    
    Parameters:
    img_i (PIL.Image): 原始图像
    selected_cards (list): (label, x, y, w, h, ...)元组列表
    border_width (int): 边框线宽（像素），默认3，高分辨率建议设为6-10
    font_size (int): 字体大小（像素），默认14，高分辨率建议设为24-32
    font_path (str): 可选字体文件路径
    
    Returns:
    PIL.Image: 添加标注后的新图像
    """
    new_img = img_i.copy()
    draw = ImageDraw.Draw(new_img)
    
    # 使用 matplotlib 的颜色循环（支持扩展颜色）
    base_colors = plt.cm.tab20.colors + plt.cm.tab20b.colors + plt.cm.tab20c.colors
    colors = [tuple(int(255*c) for c in color[:3]) for color in base_colors]

    # 字体加载逻辑（支持高分辨率适配）
    font = None
    font_loaders = [
        lambda: ImageFont.truetype(font_path, font_size) if font_path else None,
        lambda: ImageFont.truetype("arial.ttf", font_size),
        lambda: ImageFont.truetype("LiberationSans-Regular.ttf", font_size),
        lambda: ImageFont.load_default().font_variant(size=font_size)
    ]
    
    for loader in font_loaders:
        try:
            font = loader()
            if font: break
        except Exception:
            continue

    for card in selected_cards:
        label = int(card[0])
        x, y, w, h = card[1], card[2], card[3], card[4]
        
        # 自动颜色分配
        color = colors[label % len(colors)]
        
        # 绘制边界框
        draw.rectangle(
            [(x, y), (x + w, y + h)],
            outline=color,
            width=border_width  # 使用参数化线宽
        )
        
        # 标签文本处理
        text = str(label)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        # 动态位置调整（避免超出图像边界）
        text_x = x
        text_y = max(0, y - text_h)  # 顶部边界保护
        
        # 绘制带背景的标签
        draw.rectangle(
            [(text_x, text_y), (text_x + text_w, text_y + text_h)],
            fill=color
        )
        draw.text(
            (text_x, text_y),
            text,
            fill="white",
            font=font,
            stroke_width=border_width//3,  # 文字描边增强可读性
            stroke_fill=color
        )
    
    return new_img

if __name__ == '__main__':
    original_img = Image.open("./screenshot.png")
    # 模拟测试数据（label, x, y, w, h, ...）
    test_cards = [
        (0, 100, 100, 50, 30, 0, 0),
        (5, 200, 150, 60, 40, 0, 0),
        (15, 300, 200, 55, 35, 0, 0),
        (21, 400, 250, 45, 25, 0, 0)  # 测试颜色循环
    ]

    # 应用标注
    result_img = image_bbox_overlay(original_img, test_cards, border_width=8, font_size=28)

    # 保存结果
    result_img.save("annotated_image.jpg")