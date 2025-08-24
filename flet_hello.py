from main_entry import *
import base64
from io import BytesIO



import flet as ft
import time

from app.yang.yang_cv_recognizer import YangCvRecognizer
from app.yang.yang_yolo_recognizer import YangRecognizer
from app.yang.yang_hstate import YangHiddenState
from app.yang.yang_react import YangReact

from app.yang.img_utils import image_overlay, image_bbox_overlay

from flet import Image, Text, Column, Row, Container, alignment, padding

global clicked

def create_table(hstate):
    """
    创建一个 4x4 的表格，并在每个单元格中显示图片和数字。

    Parameters:
    hstate (dict): 包含 "pool" 字典的状态。

    Returns:
    Column: 包含 4x4 表格的 Column 控件。
    """
    table = Column(alignment=alignment.center, spacing=10)

    for row in range(4):
        row_container = Row(alignment=alignment.center, spacing=10)
        for col in range(4):
            index = row * 4 + col
            image_path = f"./images/cards/{index}.png"
            number = hstate["pool"].get(index, 0)

            # 创建一个容器来放置图片和数字
            cell_container = Container(
                content=Column(
                    controls=[
                        Image(src=image_path, width=45, height=45),
                        Text(value=str(number), size=16, text_align="center")
                    ],
                    alignment=alignment.center,
                    horizontal_alignment=alignment.center,
                    spacing=5
                ),
                width=60,
                height=80,
                border=ft.border.all(1, ft.colors.BLACK),
                alignment=alignment.center,
                padding=padding.all(0)
            )

            row_container.controls.append(cell_container)
        table.controls.append(row_container)

    return table

def update_table(table, hstate):
    """
    更新表格中的图片和数字。

    Parameters:
    table (Column): 包含 4x4 表格的 Column 控件。
    hstate (dict): 包含 "pool" 字典的状态。
    """
    for row_idx, row_container in enumerate(table.controls):
        for col_idx, cell_container in enumerate(row_container.controls):
            index = row_idx * 4 + col_idx
            image_path = f"./images/cards/{index}.png"
            number = hstate["pool"].get(index, [0, 0, 0])[2]

            # 更新图片和数字
            cell_container.content.controls[0].src = image_path
            cell_container.content.controls[1].value = str(number)
            print(row_idx, col_idx, index, image_path, number)

    table.update()


def perceive_recognize(sleep_seconds=3):
    # 感知并识别
    
    window_title = "羊了个羊"  # 微信窗口的部分标题
    output_path = "screenshot.png"
    print(f"正在截取窗口 '{window_title}' 的截图... 延迟 {sleep_seconds} 秒")
    time.sleep(sleep_seconds)

    coords, img = capture_window(window_title, output_path)
    if coords:
        left, top, width, height = coords
        print(f"窗口坐标: 左上角 ({left}, {top}), 宽度 {width}, 高度 {height}")
    else:
        exit(-1)

    XYWHN = (0.05, 0.19, 0.9, 0.68)
    crop_im = crop_image(img, xywhn=XYWHN)
    crop_im.save('crop_im.png')
    return img, crop_im, coords

def evaluate(hstate: YangHiddenState):

    max_score_left = sum(hstate.get_each_remaining_cards()) / 3
    print("hstate:", hstate._hstate)
    print("max score left", max_score_left)

    reward = loop_for_rewards(hstate, loop_num=10)
    progress = (reward + hstate.score) / (max_score_left + hstate.score) 
    return reward, progress

def main(page: ft.Page):
    page.title = "Images Example"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 960
    page.window.height = 720 # 960
    page.window.resizable = True
    page.padding = 50
    page.update()

    yang_recog = YangCvRecognizer()
    yang_recog_2 = YangRecognizer("runs/detect/train3/weights/best.pt")
    yang_react = YangReact()

    image_row = ft.Row(expand=1, wrap=False, scroll="always")
    reward_txt = ft.Text(f"Reward: -1", size=70, weight=ft.FontWeight.W_900, selectable=True)
    progress_txt = ft.Text("Progress:...")
    progress_pb = ft.ProgressBar(width=600)

    ori_image, crop_im, coords = perceive_recognize(sleep_seconds=1)
    # 获取图像的 base64 编码
    buffered = BytesIO()
    crop_im.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # with open("crop_im.png", "rb") as img_file:
    #     img_data = img_file.read()
    # import PIL
    # crop_im = PIL.Image.open(BytesIO(img_data))

    img = ft.Image(
        src_base64=img_base64,
        # src=f"crop_im.png",
        width=crop_im.size[0] / 4,
        height=crop_im.size[1] / 4,
        fit=ft.ImageFit.CONTAIN,
    )

    mcts_text = ft.Text("MCTS")
    img2 = ft.Image()

    table = create_table({"pool": {}})

    image_row.controls.append(img)
    image_row.controls.append(img2)
    image_row.controls.append(table)

    page.add(image_row)
    page.add(mcts_text)
    page.update()

    result = yang_recog.recognize(ori_image)
    result2 = yang_recog_2.recognize(ori_image)

    hstate = result.result

    # reward, progress = evaluate(hstate)

    yang_react.react(result2)

    clicked = False

    # def plus_click(e):
    #     clicked = True
    #     print("clicked")

    def plus_click(e):
        while True:
            ori_image, crop_im, coords = perceive_recognize(sleep_seconds=0)
            # 获取图像的 base64 编码
            buffered = BytesIO()
            crop_im.save(buffered, format="PNG")
            img.src_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # 识别 & 评估
            # result = yang_recog.recognize(ori_image)
            result2 = yang_recog_2.recognize(ori_image)
            hstate = result2.result
            # reward, progress = evaluate(hstate)
            reward, progress = "nan", 0

            # 更新 table
            hstate = yang_react.mcts.root_node.state._cached_hstate
            update_table(table, hstate._hstate)

            # if not clicked:
            #     print("Not click sleep 1")
            #     time.sleep(1)
            #     continue

            chosen_node = yang_react.react(result2)

            action_hint_img = image_overlay(crop_im, [chosen_node.action])
            # buffered = BytesIO()
            # action_hint_img.save(buffered, format="PNG")
            # img.src_base64 = base64.b64encode(buffered.getvalue()).decode()

            mcts_text.value = yang_react.mcts.stats()

            # 根节点示例
            _state = yang_react.mcts.root_node.state
            _cards = _state._cached_pool_cards + _state._cached_queue_cards
            action_bbox_img = image_bbox_overlay(action_hint_img, _cards, border_width=8, font_size=36)
            buffered = BytesIO()
            action_bbox_img.save(buffered, format="PNG")
            img.src_base64 = base64.b64encode(buffered.getvalue()).decode()

            # 选中的节点可视化
            _state = chosen_node.state
            _node_img = _state.get_crt_img()
            _next_action_node_img = image_bbox_overlay(_node_img, _state._cached_pool_cards, border_width=8, font_size=36)
            buffered = BytesIO()
            _next_action_node_img.save(buffered, format="PNG")
            img2.src_base64 = base64.b64encode(buffered.getvalue()).decode()

            # 更新奖赏
            reward_txt.value = f"Reward: {reward}"
            progress_txt.value = f"Progress: {progress*100:.2f}%"
            progress_pb.value = progress
            page.update()

            action = yang_react.cvt(result2, chosen_node)
            print("Action is :", action)
            action.execute(coords)

            time.sleep(1.5)
            # break

    # page.add(reward_txt)

    page.add(
        ft.Row([progress_txt, progress_pb]),
        ft.Row(
            [
                ft.IconButton(ft.Icons.ADD, on_click=plus_click),
                reward_txt,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    # for i in range(0, 10):
    #     images.controls.append(
    #         ft.Image(
    #             src=f"./images/cards/{i}.png",
    #             # src=f"https://picsum.photos/200/200?{i}",
    #             width=200,
    #             height=200,
    #             fit=ft.ImageFit.NONE,
    #             repeat=ft.ImageRepeat.NO_REPEAT,
    #             border_radius=ft.border_radius.all(10),
    #         )
    #     )
    page.update()

    # run_forever(0)

ft.app(main)