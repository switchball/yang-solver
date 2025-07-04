import flet as ft
import base64
import json
import uuid
from io import BytesIO
from PIL import Image

class RegionEditor(ft.UserControl):
    def __init__(self, image_src, image_src_base64, image_width=None, image_height=None, regions=None):
        super().__init__()
        self.image_src = image_src
        self.image_src_base64 = image_src_base64
        self.img_width = image_width
        self.img_height = image_height
        self.regions = regions or []
        self.rectangles = []  # 存储所有的矩形控件
        self.current_rect = None  # 当前正在绘制的矩形
        self.drag_start = None  # 拖拽起点坐标
        self.last_drag_position = {"x": 0, "y": 0}  # 最后拖拽位置

    def build(self):        
        # 用于展示相对坐标
        self.coords_text = ft.Text(
            f"{len(self.regions)}个选区区域" if self.regions else "当前没有选区",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.PRIMARY
        )
        
        # 创建可交互的画布
        self.canvas = ft.GestureDetector(
            content=ft.Image(
                src=self.image_src,
                src_base64=self.image_src_base64,
                width=self.img_width,
                height=self.img_height,
                fit=ft.ImageFit.COVER
            ),
            on_pan_start=self.on_pan_start,
            on_pan_update=self.on_pan_update,
            on_pan_end=self.on_pan_end,
            mouse_cursor=ft.MouseCursor.BASIC
        )
        
        self.canvas_stack = ft.Stack(
            controls=[self.canvas],
            width=self.img_width,
            height=self.img_height
        )
        
        # UI 组件
        return self.build_interface()
    
    def build_interface(self):
        # 操作按钮区域
        buttons_container = ft.Container(
            content=ft.Row([
                ft.OutlinedButton(
                    icon=ft.icons.DELETE,
                    text="清除全部选区",
                    on_click=self.delete_all_rects,
                    tooltip="删除所有绘制的选区",
                    width=180
                ),
                ft.FilledButton(
                    icon=ft.icons.CLOSE,
                    text="取消",
                    on_click=self.cancel_editing,
                    tooltip="取消编辑并关闭窗口",
                    width=120,
                    style=ft.ButtonStyle(bgcolor=ft.colors.RED_700)
                ),
                ft.FilledButton(
                    icon=ft.icons.SAVE,
                    text="保存选区",
                    on_click=self.save_and_close,
                    tooltip="保存选区并关闭编辑窗口",
                    width=150,
                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700)
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=10),
            alignment=ft.alignment.center
        )
        
        # 创建信息面板
        info_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("选区信息", weight=ft.FontWeight.BOLD, size=16),
                    ft.Divider(),
                    ft.Container(
                        content=self.coords_text,
                        height=200,
                    ),
                    ft.Text("坐标值为相对于图像尺寸的比例（0到1之间）", 
                           size=12, italic=True, color=ft.colors.GREY),
                ], spacing=10),
                padding=15,
            ),
            elevation=5,
            width=self.img_width,
        )
    
        # 使用说明
        tutorial = ft.Container(
            content=ft.Column([
                ft.Text("使用说明", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("■ 拖动鼠标创建矩形选区", 
                       style=ft.TextStyle(color=ft.colors.BLUE_GREY_800)),
                ft.Text("■ 可创建多个不同大小的选区", 
                       style=ft.TextStyle(color=ft.colors.BLUE_GREY_800)),
                ft.Text("■ 保存后选区将添加到主页面", 
                       style=ft.TextStyle(color=ft.colors.BLUE_GREY_800)),
                ft.Text(f"当前图像尺寸: {self.img_width}×{self.img_height} 像素", 
                       size=12, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.colors.BLUE_GREY_100),
            border_radius=5,
            bgcolor=ft.colors.WHITE,
            width=self.img_width
        )
    
        # 编辑区域布局
        return ft.Column(
            [
                # 标题
                ft.Container(
                    content=ft.Text("编辑图像选区", 
                                   style=ft.TextThemeStyle.TITLE_MEDIUM),
                    alignment=ft.alignment.center,
                    padding=10
                ),

                # 顶部操作按钮
                buttons_container,

                # 图像区域
                ft.Container(
                    content=self.canvas_stack,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20)
                ),
                
                # 教程
                ft.Container(
                    content=tutorial,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20)
                ),
                
                # 坐标信息卡片
                ft.Container(
                    content=info_card,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20)
                ),
                
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO
        )
    
    def did_mount(self):
        # 在控件挂载到页面后加载保存的选区
        self.load_saved_regions()
    
    def load_saved_regions(self):
        """加载已保存的选区"""
        # 确保画布已经创建
        if not hasattr(self, 'canvas_stack'):
            return
        
        # 清除当前选区（如果有）
        # 保留基本画布控件（索引0）
        while len(self.canvas_stack.controls) > 1:
            self.canvas_stack.controls.pop()
        
        # 重置矩形列表
        self.rectangles = []
        
        for region in self.regions:
            # 计算实际坐标
            left = region["x"] * self.img_width
            top = region["y"] * self.img_height
            width = region["width"] * self.img_width
            height = region["height"] * self.img_height
            
            # 创建矩形指示器
            rect = ft.Container(
                width=width,
                height=height,
                left=left,
                top=top,
                border=ft.border.all(2, region.get("color", "#1e88e5")),
                bgcolor=ft.colors.with_opacity(0.1, region.get("color", "#1e88e5")),
                tooltip=json.dumps(region)
            )
            
            self.canvas_stack.controls.append(rect)
            self.rectangles.append(rect)
        
        self.canvas_stack.update()
        self.update_coords_text()
    
    # 添加矩形框的函数
    def show_rect(self, left, top, width, height):
        """创建一个半透明矩形来标记选区"""
        return ft.Container(
            width=width,
            height=height,
            left=left,
            top=top,
            border=ft.border.all(2, ft.colors.RED),
            bgcolor=ft.colors.with_opacity(0.15, ft.colors.AMBER),
        )
    
    # 更新坐标显示的文本
    def update_coords_text(self):
        """更新选区信息显示"""
        if not self.rectangles:
            self.coords_text.value = "当前没有选区"
        else:
            text_lines = [f"共创建 {len(self.rectangles)} 个选区："]
            for i, rect_container in enumerate(self.rectangles):
                # 提取控件中的矩形数据（存储在tooltip中）
                if rect_container.tooltip:
                    try:
                        region_data = json.loads(rect_container.tooltip)
                        text_lines.append(f"{i+1}. [({region_data['x']:.3f}, {region_data['y']:.3f}) "
                                        f"宽: {region_data['width']:.3f}, 高: {region_data['height']:.3f}]")
                    except:
                        text_lines.append(f"{i+1}. 坐标信息无效")
                else:
                    text_lines.append(f"{i+1}. 坐标信息无效")
            
            self.coords_text.value = "\n".join(text_lines)
        self.coords_text.update()
    
    # 鼠标按下事件
    def on_pan_start(self, e: ft.DragStartEvent):
        if self.drag_start is None:  # 避免重复按下
            self.drag_start = [e.local_x, e.local_y]
            self.current_rect = self.show_rect(e.local_x, e.local_y, 0, 0)
            self.canvas_stack.controls.append(self.current_rect)
            self.last_drag_position["x"] = e.local_x
            self.last_drag_position["y"] = e.local_y
            self.canvas_stack.update()
    
    # 鼠标拖动事件
    def on_pan_update(self, e: ft.DragUpdateEvent):
        if self.drag_start is None or not self.current_rect:
            return
        
        self.last_drag_position["x"] = e.local_x
        self.last_drag_position["y"] = e.local_y
        
        start_x, start_y = self.drag_start
        width = abs(e.local_x - start_x)
        height = abs(e.local_y - start_y)
        
        # 计算矩形左上角位置
        self.current_rect.left = min(start_x, e.local_x)
        self.current_rect.top = min(start_y, e.local_y)
        self.current_rect.width = width
        self.current_rect.height = height
        self.canvas_stack.update()
    
    # 鼠标释放事件
    def on_pan_end(self, e):
        if self.drag_start is None or not self.current_rect:
            return
        
        end_x, end_y = self.last_drag_position["x"], self.last_drag_position["y"]
        start_x, start_y = self.drag_start
        
        # 确保选区有效(最小5像素)
        if abs(end_x - start_x) < 5 or abs(end_y - start_y) < 5:
            # 移除无效选区
            self.canvas_stack.controls.remove(self.current_rect)
            self.canvas_stack.update()
            self.drag_start = None
            self.current_rect = None
            return
        
        # 计算归一化坐标
        left = min(start_x, end_x) / self.img_width
        top = min(start_y, end_y) / self.img_height
        width = abs(end_x - start_x) / self.img_width
        height = abs(end_y - start_y) / self.img_height
        
        # 创建一个唯一ID用于标识选区
        region_id = str(uuid.uuid4())
        
        # 保存选区数据
        region_data = {
            "id": region_id,
            "x": left,
            "y": top,
            "width": width,
            "height": height,
            "color": "#e53935"  # 红色
        }
        
        # 保存坐标到矩形的tooltip属性
        self.current_rect.tooltip = json.dumps(region_data)
        
        # 保存到选区列表
        self.rectangles.append(self.current_rect)
        self.regions.append(region_data)
        
        # 更新显示
        self.update_coords_text()
        
        # 重置拖拽状态
        self.drag_start = None
        self.current_rect = None
    
    # 删除所有选区(包括界面上的和内存中的)
    def delete_all_rects(self, e):
        # 从堆栈中移除所有选区（只保留基本画布）
        self.canvas_stack.controls = [self.canvas_stack.controls[0]]
        
        # 重置状态
        self.rectangles = []
        self.regions = []
        
        # 更新显示
        self.canvas_stack.update()
        self.update_coords_text()
    
    # 保存选区并关闭编辑器
    def save_and_close(self, e):
        # 回调到父组件
        if hasattr(self.page, "return_regions"):
            self.page.return_regions(self.regions)
        
        # 关闭对话框
        self.page.dialog.open = False
        self.page.update()
    
    # 取消编辑
    def cancel_editing(self, e):
        # 关闭对话框不保存
        self.page.dialog.open = False
        self.page.update()
    
    # 获取当前选区
    def get_regions(self):
        return self.regions


def main(page: ft.Page):
    page.title = "图像区域标注工具"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 700
    page.bgcolor = ft.colors.GREY_100
    
    # 主页面存储的选区
    saved_regions = []
    # image_width = 400
    # image_height = 600
    image_src = "https://cataas.com/cat?width=400&height=600"
    image_src = None
    image_height = None
    image_width = None
    LOCAL_IMAGE_PATH = "crop_im.png"
    
    # 主页面图像显示 - 用于显示选区结果
    def create_region_indicator(region):
        """创建一个区域指示器组件"""
        if "x" not in region or "y" not in region:
            return None
            
        return ft.Container(
            width=region["width"] * image_width,
            height=region["height"] * image_height,
            left=region["x"] * image_width,
            top=region["y"] * image_height,
            border=ft.border.all(2, region.get("color", "#1e88e5")),
            bgcolor=ft.colors.with_opacity(0.1, region.get("color", "#1e88e5")),
            tooltip=f"位置: ({region['x']:.3f}, {region['y']:.3f})\n"
                   f"尺寸: {region['width']:.3f} × {region['height']:.3f}\n"
                   f"ID: {region.get('id', 'N/A')}"
        )
    
    # 读取本地图片并转换为 base64
    try:
        # 用二进制模式打开图片文件
        with open(LOCAL_IMAGE_PATH, "rb") as img_file:
            img_data = img_file.read()
            # 读取图片内容并进行 base64 编码
            encoded_image = base64.b64encode(img_data).decode("utf-8")
            # 转换为可以直接用于图像标签的 data URI
            image_src_base64 = f"{encoded_image}"

        img = Image.open(BytesIO(img_data))
        orig_width, orig_height = img.size
        image_width = orig_width * 0.5
        image_height = orig_height * 0.5
    except FileNotFoundError:
        # 如果图片不存在，使用一个空的 base64 占位
        image_src_base64 = "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
        page.show_snack_bar(ft.SnackBar(
            ft.Text(f"找不到图片文件: {LOCAL_IMAGE_PATH}", color=ft.colors.WHITE),
            bgcolor=ft.colors.RED,
            duration=2000
        ))

    # 创建主图像显示
    main_image = ft.Image(
        src=image_src,
        src_base64=image_src_base64,
        width=image_width,
        height=image_height,
        fit=ft.ImageFit.COVER
    )

    main_image_stack = ft.Stack(
        controls=[main_image],
        width=image_width,
        height=image_height
    )
    
    # 当有保存的选区时，添加指示器
    regions_text = ft.Text(
        "尚未标记任何区域",
        size=16,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )
    
    def update_main_display():
        # 重置显示
        main_image_stack.controls = [main_image]
        
        # 添加所有选区指示器
        for region in saved_regions:
            indicator = create_region_indicator(region)
            if indicator:
                main_image_stack.controls.append(indicator)
        
        # 更新计数文本
        regions_text.value = f"已标记 {len(saved_regions)} 个选区"
        if len(saved_regions) == 0:
            regions_text.value = "尚未标记任何选区"
        
        main_image_stack.update()
        regions_text.update()
    
    # 编辑选区处理
    def open_editor(e):
        # 创建编辑器实例(传入已有选区)
        editor = RegionEditor(
            image_src=image_src,
            image_src_base64=image_src_base64,
            image_width=image_width,
            image_height=image_height,
            regions=saved_regions.copy()
        )
        
        # 保存回主页面数据的回调函数
        def return_regions(regions):
            nonlocal saved_regions
            saved_regions = regions
            update_main_display()
            page.show_snack_bar(ft.SnackBar(
                ft.Text(f"成功保存 {len(regions)} 个选区", color=ft.colors.WHITE),
                bgcolor=ft.colors.GREEN,
                duration=2000
            ))
        
        # 创建并打开对话框
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("图像选区编辑器"),
            content=ft.Container(
                content=editor,
                width=700,
                height=800,
            ),
            actions_padding=20,
            actions=[ft.TextButton("关闭", on_click=editor.cancel_editing)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.padding.all(20),
            shape=ft.RoundedRectangleBorder(radius=10),
            content_padding=ft.padding.all(0),
        )
        
        # 设置回调函数
        page.return_regions = return_regions
        
        # 打开对话框
        page.dialog = dlg
        dlg.open = True
        page.update()
    
    # 清空所有选区
    def clear_regions(e):
        nonlocal saved_regions
        saved_regions = []
        update_main_display()
        page.show_snack_bar(ft.SnackBar(
            ft.Text("已清空所有选区", color=ft.colors.WHITE),
            bgcolor=ft.colors.RED,
            duration=2000
        ))
    
    # 导出数据
    def export_data(e):
        if not saved_regions:
            page.show_snack_bar(ft.SnackBar(
                ft.Text("没有可导出的选区数据", color=ft.colors.WHITE),
                bgcolor=ft.colors.RED,
                duration=2000
            ))
            return
        
        # 整理导出数据
        export_obj = {
            "image": image_src,
            "size": {
                "width": image_width,
                "height": image_height
            },
            "regions": [
                {
                    "id": r.get("id", str(uuid.uuid4())),
                    "position": {
                        "x": round(r["x"], 4),
                        "y": round(r["y"], 4)
                    },
                    "dimensions": {
                        "width": round(r["width"], 4),
                        "height": round(r["height"], 4)
                    }
                }
                for r in saved_regions
            ]
        }
        
        json_data = json.dumps(export_obj, indent=2)
        
        # 显示成功消息
        page.show_snack_bar(ft.SnackBar(
            ft.Text(f"成功导出 {len(saved_regions)} 个选区数据!", 
                   weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            bgcolor=ft.colors.GREEN,
            duration=3000
        ))
        
        # 打印到控制台
        print("\n导出的选区数据:")
        print(json_data)
    
    # 主页面控制区域
    control_row = ft.Row(
        [
            ft.FilledTonalButton(
                icon=ft.icons.EDIT,
                text="编辑选区",
                on_click=open_editor,
                width=150
            ),
            ft.OutlinedButton(
                icon=ft.icons.DELETE,
                text="清空选区",
                on_click=clear_regions,
                width=150
            ),
            ft.FilledTonalButton(
                icon=ft.icons.SAVE,
                text="导出数据",
                on_click=export_data,
                width=150,
                style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700)
            ),
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    # 主图像区域
    image_display = ft.Column(
        [
            control_row,
            ft.Divider(height=30),
            ft.Text("图像预览", style=ft.TextThemeStyle.TITLE_LARGE, 
                   weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Container(
                content=main_image_stack,
                padding=10,
                bgcolor=ft.colors.GREY_200,
                border_radius=ft.border_radius.all(10),
                # width=image_width + 40,
            ),
            regions_text,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.ALWAYS
    )
    
    # 主布局
    main_content = ft.Column(
        [
            ft.Container(
                ft.Text("图像区域标注工具", 
                       style=ft.TextThemeStyle.HEADLINE_SMALL, 
                       weight=ft.FontWeight.BOLD),
                padding=10,
                alignment=ft.alignment.center,
            ),
            image_display
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO
    )
    
    # 添加到页面
    page.add(main_content)
    # page.add(
    #     ft.Container(
    #         content=main_content,
    #         padding=40,
    #         bgcolor=ft.colors.WHITE,
    #         border_radius=10,
    #         shadow=ft.BoxShadow(
    #             spread_radius=1,
    #             blur_radius=10,
    #             color=ft.colors.BLUE_GREY_300,
    #             offset=ft.Offset(0, 0),
    #         )
    #     )
    # )
    
    # 初始更新
    update_main_display()

# 启动应用
ft.app(target=main)
