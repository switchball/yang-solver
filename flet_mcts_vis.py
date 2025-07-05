import flet as ft
import json
import random
import time
from collections import defaultdict, deque
import math
from typing import List, Dict
from flet.canvas import Line, Canvas

# 模拟 MCTS 节点类
class MCTSNode:
    node_id_counter = 1
    
    def __init__(self, parent=None, action=None, hidden_state=None):
        self.id = MCTSNode.node_id_counter
        MCTSNode.node_id_counter += 1
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.value = 0.0
        self.q_value = 0.0
        self.hidden_state = hidden_state or {
            "board": [[random.choice(["X", "O", "-"]) for _ in range(3)] for _ in range(3)],
            "current_player": random.choice(["X", "O"]),
            "step": random.randint(0, 8)
        }
    
    @property
    def winning_rate(self):
        return (self.value + self.visits) / (2 * self.visits) if self.visits > 0 else 0.0
    
    def add_child(self, action, hidden_state=None):
        child = MCTSNode(parent=self, action=action, hidden_state=hidden_state)
        self.children.append(child)
        return child
    
    def update(self, value):
        self.visits += 1
        self.value += value
        self.q_value = self.value / self.visits if self.visits > 0 else 0
    
    def is_fully_expanded(self):
        return len(self.children) >= 7  # 模拟有限的行动空间
    
    def is_leaf(self):
        return not self.children
    
    def __repr__(self):
        return f"Node(id={self.id}, visits={self.visits}, q={self.q_value:.2f}, win:{self.winning_rate:.1%})"

# 模拟 MCTS 算法
class MCTSAlgorithm:
    def __init__(self, root_state):
        self.root = MCTSNode(hidden_state=root_state)
        self.current_node = self.root
        self.simulation_counter = 0
        self.expansion_counter = 0
        
    def selection(self):
        # 从根节点开始，递归选择子节点直到遇到叶子节点
        node = self.root
        path = [node]
        while not node.is_leaf() and node.is_fully_expanded():
            # 使用UCT选择
            best_score = -float('inf')
            best_child = None
            
            for child in node.children:
                # UCB公式
                exploit = child.q_value
                explore = math.sqrt(2.0 * math.log(node.visits + 1) / (child.visits + 1e-6))
                score = exploit + explore
                
                if score > best_score:
                    best_score = score
                    best_child = child
            
            if best_child:
                node = best_child
                path.append(node)
            else:
                break
        
        self.current_node = node
        return path
    
    def expansion(self):
        # 如果当前节点没有被探索过，则扩展它
        if self.current_node.visits >= 1 and not self.current_node.is_fully_expanded():
            # 随机选择一个新操作
            action = f"Move {random.randint(1, 9)}"
            
            # 创建新的子节点
            new_state = json.loads(json.dumps(self.current_node.hidden_state))  # Deep copy
            new_state["board"][random.randint(0,2)][random.randint(0,2)] = self.current_node.hidden_state["current_player"]
            new_state["step"] = new_state["step"] + 1
            new_state["current_player"] = "X" if self.current_node.hidden_state["current_player"] == "O" else "O"
            
            child = self.current_node.add_child(action, new_state)
            self.expansion_counter += 1
            return child
        return None
    
    def simulation(self):
        # 模拟随机游戏直到结束
        self.simulation_counter += 1
        return random.random() * 2 - 1  # 返回一个介于-1到1之间的随机值
    
    def backpropagation(self, value, path):
        # 沿路径传播模拟结果
        for node in reversed(path):
            node.update(value)
    
    def run_iteration(self):
        # 运行一次完整的MCTS迭代
        path = self.selection()
        new_node = self.expansion()
        if new_node:
            path.append(new_node)
        
        value = self.simulation()
        self.backpropagation(value, path)
        
        # 返回用于可视化的信息
        return {
            "selected_path": [node.id for node in path],
            "expanded_node": new_node.id if new_node else None,
            "step": self.simulation_counter + self.expansion_counter
        }

# 创建棋盘的可视化表示
def create_board_ui(board, size=100):
    grid = ft.GridView(
        runs_count=3,
        max_extent=size,
        child_aspect_ratio=1.0,
        spacing=0,
        run_spacing=0
    )
    
    for i, row in enumerate(board):
        for j, cell in enumerate(row):
            border = ft.border.all(1, ft.colors.BLUE_GREY_300)
            bg_color = ft.colors.BLACK12 if (i + j) % 2 == 0 else ft.colors.WHITE
            
            grid.controls.append(
                ft.Container(
                    content=ft.Text(
                        value=cell, 
                        size=size//2, 
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.BLUE_800 if cell == "X" else ft.colors.RED_800
                    ),
                    bgcolor=bg_color,
                    border=border,
                    alignment=ft.alignment.center
                )
            )
    
    return grid

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
        root_state = {
            "board": [["-", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]],
            "current_player": "X",
            "step": 0
        }
        self.mcts = MCTSAlgorithm(root_state)
        self.page.update()
        
        # 可视化组件
        self.tree_visualization = ft.Container(
            ref=self.tree_visualization_ref,
            width=1100,
            height=800,
            bgcolor=ft.colors.WHITE10,
            padding=20,
            border_radius=10,
            border=ft.border.all(1, ft.colors.BLUE_GREY_400),
            content=ft.Column(expand=True)
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
                        ft.ProgressBar(width=300, height=10, value=0, color=ft.colors.GREEN, bgcolor=ft.colors.GREEN_100)
                    ]
                ),
                padding=15
            )
        )
        
        self.controls1 = ft.Row([
            ft.ElevatedButton(
                "单步执行", 
                on_click=self.step_forward,
                icon=ft.icons.SKIP_NEXT_OUTLINED
            ),
            ft.FilledButton("完整视图", icon=ft.icons.ZOOM_OUT_MAP, 
                               on_click=self.show_full_tree_view),
            ft.ElevatedButton(
                "连续运行N步", 
                on_click=self.n_step_forward,
                icon=ft.icons.PLAY_ARROW_OUTLINED
            ),
            ft.ElevatedButton(
                "重置", 
                on_click=self.reset,
                icon=ft.icons.RESTART_ALT_OUTLINED
            ),
        ], spacing=10)

        self.controls2 = ft.Row([
            ft.Text("选择步数 (N):"),
            ft.Slider(
                min=1,
                max=100,
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
            bgcolor=ft.colors.WHITE10,
            padding=15,
            border_radius=10,
            border=ft.border.all(1, ft.colors.BLUE_GREY_400),
            content=ft.Text("选择一个节点查看详情", size=16)
        )
        
        # 布局
        left_panel = ft.Column([
            self.controls1,
            self.controls2,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            self.stats_panel,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
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
        
    def build_tree_graph(self) -> List[ft.Control]:
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
                child_x = x_offset - (child_count - 1) * 20 + i * 40

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
        spacing = 60
        
        # 为每个节点创建位置映射
        positions = {}
        for level, nodes in levels.items():
            total_nodes = len(nodes)
            for i, (node_id, x_offset, parent_id) in enumerate(nodes):
                y = level * spacing + 60
                x = tree_width // 2 + x_offset * 2.5
                positions[node_id] = (x, y)
                
                # 如果存在父节点，画一条线
                if parent_id in positions:
                    parent_x, parent_y = positions[parent_id]
                    lines.append(
                        Line(  # 使用从 flet.canvas 导入的 Line
                            x1=parent_x, y1=parent_y + 15,
                            x2=x, y2=y - 15,
                            paint=ft.Paint(
                                color=ft.colors.BLUE_GREY_300,
                                stroke_width=1.5
                            )
                        )
                    )
        
        canvas.shapes = lines  # 将线条添加到 Canvas
        
        # 创建节点容器
        node_containers = []
        for node_id, (x, y) in positions.items():
            node = self.all_nodes[node_id]
            bg_color = (ft.colors.BLUE_100 
                        if node == self.mcts.current_node else 
                        ft.colors.BLUE_GREY_100)
            border_color = (ft.colors.BLUE_600 
                            if node == self.mcts.current_node else 
                            ft.colors.BLUE_GREY_400)
            
            node_containers.append(
                ft.Container(
                    width=80,
                    height=30,
                    top=y - 15,
                    left=x - 40,
                    bgcolor=bg_color,
                    border_radius=8,
                    border=ft.border.all(2, border_color),
                    on_click=lambda e, n=node: self.show_node_details(n),
                    content=ft.Column([
                        ft.Text(
                            f"{node.id}: {node.visits}/{node.q_value:.2f}", 
                            tooltip=f"{node.id}: {node.visits} visits, Q-value: {node.q_value:.2f} #Child: {len(node.children)}\n" 
                                    f"Win: {node.winning_rate:.0%}",
                            size=9),
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
    
    def _get_path_to_root(self, node: MCTSNode) -> list:
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
    
    def _get_all_descendants(self, node: MCTSNode) -> set:
        """获取指定节点的所有后代（包括子节点、孙节点等）集合"""
        descendants = set()
        queue = deque([node])
        
        while queue:
            current = queue.popleft()
            for child in current.children:
                descendants.add(child)
                queue.append(child)
                
        return descendants

    def show_node_details(self, node: MCTSNode):
        board_ui = create_board_ui(node.hidden_state["board"])
        
        details = ft.Column([
            ft.Row([
                ft.Text(f"节点ID: {node.id}", size=14, weight=ft.FontWeight.BOLD, 
                        color=ft.colors.BLUE_700),
                ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE_400)
            ]),
            ft.Text(f"访问次数: {node.visits}", size=14),
            ft.Text(f"累计价值: {node.value:.2f}", size=14),
            ft.Text(f"平均价值: {node.q_value:.2f}", size=14),
            ft.Text(f"赢率: {node.winning_rate:.1%}", size=14, color=ft.colors.GREEN_700),
            ft.Divider(height=10),
            ft.Text("当前局面:", weight=ft.FontWeight.BOLD),
            board_ui,
            ft.Divider(height=10),
            ft.Text("隐藏状态:", weight=ft.FontWeight.BOLD),
            ft.Text(
                json.dumps({k: v for k, v in node.hidden_state.items() if k != "board"}, 
                          indent=2), 
                size=12, 
                selectable=True
            )
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
        
        # 重新注册整个树结构（确保所有节点都在 all_nodes 中）
        self.all_nodes = {}  # 先清空字典
        self.register_node(self.mcts.root)
        
        self.update_tree_visualization()

    def n_step_forward(self, e: ft.ControlEvent):
        # 执行一次迭代
        for i in range(self.step_count):
            result = self.mcts.run_iteration()
        
        # 重新注册整个树结构（确保所有节点都在 all_nodes 中）
        self.all_nodes = {}  # 先清空字典
        self.register_node(self.mcts.root)
        
        self.update_tree_visualization()

        self.page.show_snack_bar(ft.SnackBar(
            ft.Text(f"已连续运行 {self.step_count} 步", color=ft.colors.WHITE),
            bgcolor=ft.colors.GREEN,
            duration=1000
        ))

    # 递归注册节点的方法
    def register_node(self, node: MCTSNode):
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
        root_state = {
            "board": [["-", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]],
            "current_player": "X",
            "step": 0
        }
        MCTSNode.node_id_counter = 1
        self.mcts = MCTSAlgorithm(root_state)
        self.all_nodes = {}
        self.register_node(self.mcts.root)
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
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.scroll = ft.ScrollMode.ADAPTIVE
    visualizer = MCTSVisualizer(page)

ft.app(target=main)
