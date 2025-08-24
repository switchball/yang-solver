import flet as ft
import json
import random
import time
from collections import defaultdict, deque
import math
from typing import List, Dict
from flet.canvas import Line, Canvas
from search.mcts import MCTS
from search.tree_node import TreeNode
from app.yang.logic.yang_tree_node import YangTreeNode
from app.yang.logic.yang_simulator import YangSimulator
from app.yang.yang_yolo_recognizer import YangYOLORecognizer
from app.yang.yang_constants import MCTS_ROLLOUT_BATCH_SIZE

from visual_tree_node import VisualTreeNode
import os
import base64
from PIL import Image

# 真实 MCTS 算法包装器
class RealMCTSAlgorithm:
    def __init__(self):
        # 初始化羊羊模拟器
        model_path = "runs/detect/train3/weights/best.pt"
        self.recognizer = YangYOLORecognizer(model_path)
        
        # 创建根节点 - 使用crop_im.png作为初始状态
        from PIL import Image
        root_image = Image.open("crop_im.png")
        from app.yang.logic.yang_board_state import YangBoardState
        root_state = YangBoardState(root_image, last_hstate=None, simulator=self.recognizer)
        real_root = YangTreeNode(state=root_state)
        
        # 初始化真实MCTS
        self.mcts = MCTS(
            root_node=real_root,
            rollout_policy=self.rollout_policy,
            rollout_iterations=MCTS_ROLLOUT_BATCH_SIZE,
            node_clz=YangTreeNode
        )
        
        # 可视化根节点
        self.visual_root = VisualTreeNode(real_root)
        self.current_visual_node = self.visual_root
        
        # 计数器
        self.simulation_counter = 0
        self.expansion_counter = 0
        
    def rollout_policy(self, node):
        """Rollout policy using real implementation from yang_react.py"""
        self.simulation_counter += 1
        # 使用真实rollout策略
        from app.yang.yang_react import fast_rollout_policy
        score = fast_rollout_policy(node)
            
        return score

    def run_iteration(self, run_step=1):
        """运行一次完整的MCTS迭代"""
        # 运行真实MCTS迭代
        self.mcts.run(run_step)
        
        # 更新可视化树
        self._update_visual_tree()
        
        # 返回用于可视化的信息
        return {
            "step": self.simulation_counter + self.expansion_counter
        }
        
    def _update_visual_tree(self):
        """更新可视化树结构以匹配真实MCTS树"""
        # 清空现有可视化树
        self.visual_root = VisualTreeNode(self.mcts.root_node)
        self.current_visual_node = self.visual_root
        
        # 递归添加子节点
        self._add_children(self.mcts.root_node, self.visual_root)
    
    def _add_children(self, real_node: TreeNode, visual_node: VisualTreeNode):
        """递归添加子节点到可视化树"""
        if real_node in self.mcts.children:
            for real_child in self.mcts.children[real_node]:
                visual_child = visual_node.add_child(real_child)
                self._add_children(real_child, visual_child)

    @property
    def root(self):
        return self.visual_root

    def reset(self):
        """重置MCTS树"""
        # 初始化羊羊模拟器
        model_path = "runs/detect/train3/weights/best.pt"
        self.recognizer = YangYOLORecognizer(model_path)
        
        # 创建根节点 - 使用crop_im.png作为初始状态
        from PIL import Image
        root_image = Image.open("crop_im.png")
        from app.yang.logic.yang_board_state import YangBoardState
        root_state = YangBoardState(root_image, last_hstate=None, simulator=self.recognizer)
        real_root = YangTreeNode(state=root_state)
        
        # 初始化真实MCTS
        self.mcts = MCTS(
            root_node=real_root,
            rollout_policy=self.rollout_policy,
            rollout_iterations=MCTS_ROLLOUT_BATCH_SIZE,
            node_clz=YangTreeNode
        )
        
        # 可视化根节点
        self.visual_root = VisualTreeNode(real_root)
        self.current_visual_node = self.visual_root
        
        # 计数器
        self.simulation_counter = 0
        self.expansion_counter = 0

# 创建棋盘的可视化表示（支持图像加载）
def create_board_ui(state, size=100):
    # 检查是否有图像数据
    try:
        # 将图像转换为base64
        img = state.get_crt_img()
        img_width, img_height = img.size
        img_path = f"temp_board_{int(time.time())}.png"
        img.save(img_path)

        # buffered = BytesIO()
        # crop_im.save(buffered, format="PNG")
        # img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return ft.Image(
            src=img_path,
            width=img_width*0.3,
            height=img_height*0.3,
            fit=ft.ImageFit.CONTAIN
        )
    except Exception as e:
        print(f"图像加载失败: {str(e)}")


# MCTS 可视化工具
class MCTSVisualizer:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "MCTS 算法可视化工具"
        self.page.padding = 20
        self.page.window_width = 1400
        self.page.window_height = 800
        
        # 添加新的步数相关属性
        self.step_count = 100  # 默认运行步数
        self.total_steps_completed = 0  # 总步数统计

        # 初始化控件引用
        self.iterations_ref = ft.Ref[ft.Text]()
        self.node_count_ref = ft.Ref[ft.Text]()
        self.expansions_ref = ft.Ref[ft.Text]()
        self.simulations_ref = ft.Ref[ft.Text]()
        self.tree_visualization_ref = ft.Ref[ft.Container]()
        self.node_detail_ref = ft.Ref[ft.Container]()
        self.speed_slider_ref = ft.Ref[ft.Slider]()
        self.stats_container_ref = ft.Ref[ft.Column]()
        
        # 初始化MCTS算法
        self.mcts = RealMCTSAlgorithm()
        self.page.update()
        
        # 可视化组件（添加手势检测）
        self.tree_visualization = ft.GestureDetector(
            on_pan_start=self.handle_right_pan_start,
            on_pan_update=self.handle_right_pan_update,
            on_pan_end=self.handle_right_pan_end,
            content=ft.Container(
                ref=self.tree_visualization_ref,
                width=1100,
                height=800,
                bgcolor=ft.Colors.BLUE_GREY_900,
                padding=20,
                border_radius=10,
                border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
                content=ft.Column(expand=True)
            )
        )
        
        self.stats_panel = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    ref=self.stats_container_ref,
                    controls=[
                        ft.Row([ft.Text("算法统计", size=18, weight=ft.FontWeight.BOLD)]),
                        ft.Text(ref=self.iterations_ref, value="迭代次数: 0", size=14),
                        ft.Text(ref=self.node_count_ref, value="节点总数: 1", size=14),
                        ft.Text(ref=self.expansions_ref, value="扩展次数: 0", size=14),
                        ft.Text(ref=self.simulations_ref, value="模拟次数: 0", size=14),
                        ft.ProgressBar(width=300, height=10, value=0, color=ft.Colors.GREEN, bgcolor=ft.Colors.GREEN_900)
                    ]
                ),
                padding=15
            )
        )
        
        self.controls1 = ft.Row([
            ft.ElevatedButton(
                "单步", 
                on_click=self.step_forward,
                icon=ft.Icons.SKIP_NEXT_OUTLINED
            ),
            ft.FilledButton("全图", icon=ft.Icons.ZOOM_OUT_MAP, 
                               on_click=self.show_full_tree_view),
            ft.ElevatedButton(
                "N步", 
                on_click=self.n_step_forward,
                icon=ft.Icons.PLAY_ARROW_OUTLINED
            ),
            ft.ElevatedButton(
                "重置", 
                on_click=self.reset,
                icon=ft.Icons.RESTART_ALT_OUTLINED
            ),
        ], spacing=10)

        self.controls2 = ft.Row([
            ft.Text("选择步数 (N):"),
            ft.Slider(
                min=2,
                max=200,
                divisions=99,  # 生成10个区间（100,200,...1000）
                label="N = {value}",
                value=self.step_count,
                on_change=self.slider_changed,
                expand=True,
            ),
            # ft.Container(
            #     content=ft.Text(f"N = {self.step_count}"),
            #     width=80
            # )
        ])
        
        self.node_detail = ft.Container(
            ref=self.node_detail_ref,
            height=500,
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=15,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
            content=ft.Text("选择一个节点查看详情", size=16)
        )
        
        # 布局
        left_panel = ft.Column([
            self.controls1,
            self.controls2,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.stats_panel,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Container(
                content=ft.Text("节点详情", weight=ft.FontWeight.BOLD, size=16),
                alignment=ft.alignment.top_left
            ),
            self.node_detail
        ], width=280)
        
        right_panel = ft.Column([
            ft.Container(
                content=ft.Text("蒙特卡洛树搜索 (MCTS) 可视化", 
                                weight=ft.FontWeight.BOLD, 
                                size=20,
                                text_align=ft.TextAlign.CENTER),
                alignment=ft.alignment.center
            ),
            self.tree_visualization
        ], expand=True)
        
        main_row = ft.Row([left_panel, right_panel], expand=True, spacing=20)
        
        self.page.add(main_row)
        
        # 聚焦模式
        self.focus_node = None  # 新添加：当前聚焦的节点
        self.show_full_tree = True  # 新添加：是否显示完整树（默认显示）

        # 平移相关变量
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        self.paning_ts = 0

        # 状态变量
        self.running = False
        self.speed = 0.5  # 秒
        self.all_nodes = {}
        self.register_node(self.mcts.root)
        self.update_tree_visualization()
        
        # 定时器
        self.interval = False
        self.page.on_dispose = self.stop_interval

    
    def stop_interval(self):
        if self.interval:
            self.interval.cancel()
    
    def update_tree_visualization(self):
        tree_graph = self.build_tree_graph()
        if self.tree_visualization_ref.current:
            self.tree_visualization_ref.current.content = ft.Container(
                content=ft.Stack(tree_graph, expand=True),
            )
            self.tree_visualization_ref.current.update()

        # 更新统计信息
        iteration_count = self.mcts.simulation_counter + self.mcts.expansion_counter
        if self.iterations_ref.current:
            self.iterations_ref.current.value = f"迭代次数: {iteration_count}"
            self.iterations_ref.current.update()
        if self.node_count_ref.current:
            self.node_count_ref.current.value = f"节点总数: {len(self.all_nodes)}"
            self.node_count_ref.current.update()
        if self.expansions_ref.current:
            self.expansions_ref.current.value = f"扩展次数: {self.mcts.expansion_counter}"
            self.expansions_ref.current.update()
        if self.simulations_ref.current:
            self.simulations_ref.current.value = f"模拟次数: {self.mcts.simulation_counter}"
            self.simulations_ref.current.update()
            
    def handle_right_pan_start(self, e: ft.DragStartEvent):
        self.is_panning = True
        self.pan_start_x = e.local_x
        self.pan_start_y = e.local_y
        self.paning_ts = e.timestamp
            
    def handle_right_pan_update(self, e: ft.DragUpdateEvent):
        if self.is_panning:
            self.is_panning = False
            self.pan_offset_x += (e.local_x - self.pan_start_x)
            self.pan_offset_y += (e.local_y - self.pan_start_y)
            self.pan_start_x = e.local_x
            self.pan_start_y = e.local_y
            self.update_tree_visualization()
            self.is_panning = True
            
    def handle_right_pan_end(self, e: ft.DragEndEvent):
        self.is_panning = False
        
    def build_tree_graph(self) -> List[ft.Control]:
        X_SPACING = 75  # 节点之间的水平间距
        Y_SPACING = 70  # 节点之间的垂直间距
        NODE_WIDTH = 60  # 节点的宽度
        NODE_HEIGHT = 30  # 节点的高度
        # 如果树容器尚未准备好，返回空列表
        if not self.tree_visualization_ref.current:
            return []
        
        # 重建父节点映射
        self._build_parent_map()
        
        # 获取树容器的宽度
        tree_width = self.tree_visualization_ref.current.width or 1100
        
        # 层次化节点布局
        levels: Dict[int, List] = defaultdict(list)
        max_depth = 0
        
        # 在队列初始化之前添加树的裁剪逻辑
        displayed_nodes = set() if self.show_full_tree else self._get_tree_subset_to_display()

        # 使用BFS遍历树结构
        queue = [(self.mcts.root, 0, 0, 0, True)]  # (node, level, x_offset, parent_id, should_display)
        while queue:
            node, level, x_offset, parent_id, should_display = queue.pop(0)
            levels[level].append((node.id, x_offset, parent_id))

            # 如果节点不应该显示，跳过处理（但仍保留其位置）
            if not should_display:
                continue
            
            max_depth = max(max_depth, level)
            
            # 计算是否需要显示子节点（根据当前聚焦点）
            display_children = (
                self.focus_node is None or  # 完整树模式
                node in self._get_path_to_root(self.focus_node) or  # 在到根节点的路径上
                node == self.focus_node  # 当前节点是焦点节点
            )

            # 为每个子节点安排位置
            child_count = len(node.children)
            for i, child in enumerate(node.children):
                child_x = x_offset - (child_count - 1) * X_SPACING * 0.5 + i * X_SPACING

                # 确定是否显示该子节点（不显示的子节点只是占位，不会展开其子树）
                display_child = display_children and (  # 只有当父节点设置为显示时
                    self.focus_node is None or  # 完整模式
                    child in self._get_path_to_root(self.focus_node) or  # 在到根节点的路径上
                    child == self.focus_node  # 当前子节点是焦点节点
                )

                queue.append((child, level + 1, child_x, node.id, display_child))
        
        # 创建 Canvas 用于绘制线条
        canvas = Canvas()
        lines = []  # 存储线条元素
        spacing = Y_SPACING
        
        # 为每个节点创建位置映射
        positions = {}
        for level, nodes in levels.items():
            total_nodes = len(nodes)
            for i, (node_id, x_offset, parent_id) in enumerate(nodes):
                x, y = self.pan_offset_x, self.pan_offset_y  # 使用偏移量
                y += level * spacing + spacing
                x += tree_width // 2 + x_offset * 1
                positions[node_id] = (x, y)
                
                # 如果存在父节点，画一条线
                if parent_id in positions:
                    parent_x, parent_y = positions[parent_id]
                    lines.append(
                        Line(  # 使用从 flet.canvas 导入的 Line
                            x1=parent_x, y1=parent_y + 15,
                            x2=x, y2=y - 15,
                            paint=ft.Paint(
                                color=ft.Colors.BLUE_GREY_700,
                                stroke_width=1.5
                            )
                        )
                    )
        
        canvas.shapes = lines  # 将线条添加到 Canvas
        
        # 计算最大访问次数
        max_visits = 0
        for node_id in positions:
            node = self.all_nodes[node_id]
            node_visits = math.log(node.visits + 1)
            if node_visits > max_visits:
                max_visits = node_visits
        if max_visits == 0:
            max_visits = 1

        # 创建节点容器（根据访问次数设置颜色）
        node_containers = []
        for node_id, (x, y) in positions.items():
            node = self.all_nodes[node_id]
            # 根据访问次数计算颜色强度（0-1）
            ratio = math.log(node.visits + 1) / max_visits
            
            # 生成暗色模式友好的颜色（深蓝->紫红->深橙）
            # 减少整体亮度，保持足够对比度
            r = int(200 * ratio)
            g = int(100 * ratio)
            b = int(200 * (1 - ratio))
            
            bg_color = f"#{r:02x}{g:02x}{b:02x}"
            
            border_color = (ft.Colors.BLUE_400
                            if node == self.mcts.current_visual_node else
                            ft.Colors.BLUE_GREY_500)
            
            node_containers.append(
                ft.Container(
                    width=NODE_WIDTH,
                    height=NODE_HEIGHT,
                    top=y - NODE_HEIGHT / 2,
                    left=x - NODE_WIDTH / 2,
                    bgcolor=bg_color,
                    border_radius=8,
                    border=ft.border.all(2, border_color),
                    on_click=lambda e, n=node: self.show_node_details(n),
                    content=ft.Column([
                        ft.Text(
                            f"{node.id}: {node.visits}/{node.q_value:.2f}",
                            tooltip=f"{node.id}: {node.visits} visits, Avg. Q-value: {node.avg_q_value:.2f}, Best. Q-value: {node.q_value:.2f} #Child: {len(node.children)}\n"
                                    f"Confidence: {node.confidence:.2f} UCB: {node.confidence + node.q_value:.2f}\n" 
                                    f"Children Q-Stdev: {node.children_q_stdev:.2f}"
                                    f"Win: {node.winning_rate:.0%}",
                            size=9,
                            color=ft.Colors.WHITE),  # 确保文字为白色
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )
        
        # 将 Canvas 和节点容器一起放入 Stack
        stack = ft.Stack([
            canvas,  # Canvas 作为底层
            ft.Stack(node_containers)  # 节点容器在上层
        ], expand=True)
        
        return [stack]  # 返回 Stack 控件列表

    def _build_parent_map(self):
        self.parent_map = {}
        
        # 使用BFS遍历构建父节点映射
        queue = deque([(self.mcts.root, None)])
        while queue:
            current_node, parent = queue.popleft()
            if parent:
                self.parent_map[current_node.id] = parent
                
            for child in current_node.children:
                queue.append((child, current_node))

    # 添加辅助方法
    def _get_tree_subset_to_display(self) -> set:
        """获取应该显示的节点集合（聚焦节点+路径到根）"""
        if not self.focus_node:
            return set()
        
        # 获取从根节点到当前节点的路径
        path_to_root = self._get_path_to_root(self.focus_node)
        
        # 添加聚焦节点及其所有后代
        nodes_to_display = set(path_to_root)
        nodes_to_display |= self._get_all_descendants(self.focus_node)
        
        return nodes_to_display
    
    def _get_path_to_root(self, node: TreeNode) -> list:
        """获取从指定节点到根节点的路径"""
        # 由于我们没有直接的父引用，这里使用父映射查找
        path = [node]
        current = node
        
        # 从树底部逆向追踪到根节点
        while current and current != self.mcts.root:
            parent = self.parent_map.get(current.id)
            if not parent:
                break
            path.append(parent)
            current = parent
        
        return path
    
    def _get_all_descendants(self, node: TreeNode) -> set:
        """获取指定节点的所有后代（包括子节点、孙节点等）集合"""
        descendants = set()
        queue = deque([node])
        
        while queue:
            current = queue.popleft()
            for child in current.children:
                descendants.add(child)
                queue.append(child)
                
        return descendants

    def show_node_details(self, node: VisualTreeNode):
        # 获取真实节点状态
        real_state = node.real_node.state 
        
        # 关联到达的动作
        pending_action = real_state.pending_action_list if hasattr(real_state, 'pending_action_list') else None

        # 创建棋盘UI
        board_ui = create_board_ui(
            real_state
        )
        
        # 创建hstate JSON展示
        hstate_json = json.dumps(node.hidden_state, indent=2, ensure_ascii=False)
        json_view = ft.Text(hstate_json, selectable=True, size=12)
        
        details = ft.Column([
            ft.Row([
                ft.Text(f"节点ID: {node.id}", size=14, weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.BLUE_700),
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400)
            ]),
            ft.Text(f"访问次数: {node.visits}", size=14),
            # ft.Text(f"累计价值: {node.value:.2f}", size=14),
            ft.Text(f"平均价值: {node.avg_q_value:.2f}", size=14),
            ft.Text(f"最优价值: {node.q_value:.2f}", size=14),
            # ft.Text(f"赢率: {node.winning_rate:.1%}", size=14, color=ft.Colors.GREEN_700),
            ft.Divider(height=10),
            ft.Text("当前局面:", weight=ft.FontWeight.BOLD),
            board_ui,
            ft.Divider(height=10),
            ft.Text(f"关联动作: {pending_action}", size=14),
            ft.Text("隐藏状态:", weight=ft.FontWeight.BOLD),
            json_view
        ], scroll=ft.ScrollMode.ALWAYS)
        
        if self.node_detail_ref.current:
            self.node_detail_ref.current.content = details
            self.node_detail_ref.current.update()

        # 设置新的聚焦节点
        self.focus_node = node
        self.update_tree_visualization()

    # 添加方法用于切换到完整树视图
    def show_full_tree_view(self, e: ft.ControlEvent = None):
        self.focus_node = None
        self.show_full_tree = True
        self.update_tree_visualization()

    def step_forward(self, e: ft.ControlEvent):
        # 执行一次迭代
        result = self.mcts.run_iteration()
        
        # 重置节点ID计数器
        VisualTreeNode.reset_node_counter()
        
        # 重新注册整个树结构（确保所有节点都在 all_nodes 中）
        self.all_nodes = {}  # 先清空字典
        self.register_node(self.mcts.root)
        
        self.update_tree_visualization()

    def n_step_forward(self, e: ft.ControlEvent):
        # 执行 step_count 次迭代
        result = self.mcts.run_iteration(run_step=self.step_count)
        
        # 重置节点ID计数器
        VisualTreeNode.reset_node_counter()
        
        # 重新注册整个树结构（确保所有节点都在 all_nodes 中）
        self.all_nodes = {}  # 先清空字典
        self.register_node(self.mcts.root)
        
        self.update_tree_visualization()
        
        self.page.show_snack_bar(ft.SnackBar(
            ft.Text(f"已连续运行 {self.step_count} 步", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN,
            duration=1000
        ))

    # 递归注册节点的方法
    def register_node(self, node: TreeNode):
        """递归注册节点及其所有子节点到all_nodes字典"""
        # 如果节点已注册，直接返回
        if node.id in self.all_nodes:
            return
        
        # 注册当前节点
        self.all_nodes[node.id] = node
        
        # 递归注册所有子节点
        for child in node.children:
            self.register_node(child)

    def pause(self, e: ft.ControlEvent):
        self.running = False
    
    def reset(self, e: ft.ControlEvent):
        self.running = False
        VisualTreeNode.reset_node_counter()
        self.mcts.reset()
        self.all_nodes = {}
        self.register_node(self.mcts.root)
        # 重置平移状态
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.update_tree_visualization()
        
        if self.node_detail_ref.current:
            self.node_detail_ref.current.content = ft.Text("选择一个节点查看详情", size=16)
            self.node_detail_ref.current.update()
    
    def slider_changed(self, e: ft.ControlEvent):
        """处理滑块变化事件"""
        self.step_count = int(e.control.value)
        # 立即更新UI中的N值显示
        self.update_tree_visualization()

# 启动应用
def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.scroll = ft.ScrollMode.ADAPTIVE
    visualizer = MCTSVisualizer(page)

# 清理临时图像文件
def cleanup_temp_images():
    for file in os.listdir():
        if file.startswith("temp_board_"):
            try:
                os.remove(file)
            except:
                pass

# 注册清理函数
import atexit
atexit.register(cleanup_temp_images)

ft.app(target=main)
