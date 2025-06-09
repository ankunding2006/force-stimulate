import pygame
import numpy as np
import math
from typing import List, Tuple, Optional

class Vector2D:
    """二维向量类"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def magnitude(self) -> float:
        """计算向量的模长"""
        return math.sqrt(self.x**2 + self.y**2)
    
    def angle(self) -> float:
        """计算向量的角度（弧度）"""
        return math.atan2(self.y, self.x)
    
    def angle_degrees(self) -> float:
        """计算向量的角度（度）"""
        return math.degrees(self.angle())
    
    def normalize(self) -> 'Vector2D':
        """单位化向量"""
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        """向量加法"""
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        """标量乘法"""
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __str__(self) -> str:
        return f"Vector2D({self.x:.2f}, {self.y:.2f})"

class Force:
    """力向量类"""
    def __init__(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], color: Tuple[int, int, int] = (255, 0, 0)):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.scale = 1.0  # 缩放比例，用于调整显示大小
        self.is_selected = False
        self.is_dragging = False
        
    @property
    def vector(self) -> Vector2D:
        """获取力向量"""
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        return Vector2D(dx / self.scale, dy / self.scale)
    
    @property
    def magnitude(self) -> float:
        """获取力的大小"""
        return self.vector.magnitude()
    
    @property
    def angle_degrees(self) -> float:
        """获取力的角度（度）"""
        return self.vector.angle_degrees()
    
    def contains_point(self, point: Tuple[int, int], tolerance: int = 10) -> bool:
        """检查点是否在力向量附近"""
        x, y = point
        x1, y1 = self.start_pos
        x2, y2 = self.end_pos
        
        # 计算点到线段的距离
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B) <= tolerance
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        dx = x - xx
        dy = y - yy
        return math.sqrt(dx * dx + dy * dy) <= tolerance
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """绘制力向量"""
        # 绘制力向量线
        line_width = 3 if self.is_selected else 2
        pygame.draw.line(surface, self.color, self.start_pos, self.end_pos, line_width)
        
        # 绘制箭头
        self._draw_arrow_head(surface)
        
        # 绘制数值标签
        self._draw_label(surface, font)
    
    def _draw_arrow_head(self, surface: pygame.Surface):
        """绘制箭头头部"""
        if self.magnitude < 10:  # 太短的向量不绘制箭头
            return
            
        arrow_length = 15
        arrow_angle = math.pi / 6  # 30度
        
        # 计算箭头方向
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        angle = math.atan2(dy, dx)
        
        # 计算箭头两个端点
        x1 = self.end_pos[0] - arrow_length * math.cos(angle - arrow_angle)
        y1 = self.end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
        x2 = self.end_pos[0] - arrow_length * math.cos(angle + arrow_angle)
        y2 = self.end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
        
        # 绘制箭头
        pygame.draw.polygon(surface, self.color, [self.end_pos, (x1, y1), (x2, y2)])
    
    def _draw_label(self, surface: pygame.Surface, font: pygame.font.Font):
        """绘制数值标签"""
        # 计算标签位置（在向量中点偏移）
        mid_x = (self.start_pos[0] + self.end_pos[0]) // 2
        mid_y = (self.start_pos[1] + self.end_pos[1]) // 2
        
        # 创建标签文本
        magnitude_text = f"{self.magnitude:.1f}N"
        angle_text = f"{self.angle_degrees:.1f}°"
        
        # 渲染文本
        mag_surface = font.render(magnitude_text, True, (0, 0, 0))
        angle_surface = font.render(angle_text, True, (100, 100, 100))
        
        # 绘制背景
        text_rect = pygame.Rect(mid_x - 30, mid_y - 20, 60, 30)
        pygame.draw.rect(surface, (255, 255, 255, 180), text_rect)
        pygame.draw.rect(surface, (0, 0, 0), text_rect, 1)
        
        # 绘制文本
        surface.blit(mag_surface, (mid_x - mag_surface.get_width() // 2, mid_y - 15))
        surface.blit(angle_surface, (mid_x - angle_surface.get_width() // 2, mid_y - 5))

class ForceSimulator:
    """力的合成仿真主类"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("力的合成可视化仿真")
        
        # 初始化字体 - 支持中文显示
        self.init_fonts()
        
        # 颜色定义
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GREEN = (0, 255, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (200, 200, 200)
        
        # 力向量列表
        self.forces: List[Force] = []
        self.resultant_force: Optional[Vector2D] = None
        
        # 交互状态
        self.is_creating_force = False
        self.temp_start_pos = None
        self.selected_force: Optional[Force] = None
        self.dragging_force = False
        self.drag_offset = (0, 0)
        
        # UI元素
        self.grid_size = 50
        self.show_grid = True
        self.show_components = True
        
        # 颜色循环（为不同的力分配不同颜色）
        self.force_colors = [
            (255, 0, 0),    # 红色
            (0, 0, 255),    # 蓝色
            (0, 200, 0),    # 绿色
            (255, 165, 0),  # 橙色
            (128, 0, 128),  # 紫色
            (255, 192, 203), # 粉色
        ]
        self.color_index = 0
    
    def init_fonts(self):
        """初始化字体，支持中文"""
        # 尝试使用系统中文字体
        chinese_fonts = [
            'Microsoft YaHei',      # 微软雅黑
            'SimHei',               # 黑体
            'SimSun',               # 宋体
            'KaiTi',                # 楷体
            'FangSong',             # 仿宋
            'Arial Unicode MS',     # Arial Unicode
        ]
        
        self.font = None
        self.title_font = None
        
        # 尝试找到支持中文的字体
        for font_name in chinese_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 20)
                # 测试渲染中文字符
                test_surface = test_font.render("测试", True, (0, 0, 0))
                if test_surface.get_width() > 0:  # 如果能正确渲染中文
                    self.font = pygame.font.SysFont(font_name, 20)
                    self.title_font = pygame.font.SysFont(font_name, 28)
                    print(f"使用字体: {font_name}")
                    break
            except:
                continue
        
        # 如果没有找到合适的字体，使用默认字体
        if not self.font:
            print("未找到支持中文的字体，使用默认字体")
            self.font = pygame.font.Font(None, 24)
            self.title_font = pygame.font.Font(None, 36)
        
    def run(self):
        """运行仿真"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                self.handle_event(event)
            
            self.update()
            self.draw()
            clock.tick(60)
        
        pygame.quit()
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                self.handle_left_click(event.pos)
            elif event.button == 3:  # 右键
                self.handle_right_click(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                self.handle_left_release(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event.key)

    def handle_left_click(self, pos):
        """处理左键点击"""
        center_x, center_y = self.width // 2, self.height // 2
        center_radius = 30  # 中心区域半径
        
        # 检查是否在中心区域内点击
        is_in_center = self._distance(pos, (center_x, center_y)) <= center_radius
        
        if is_in_center:
            # 在中心区域内点击，优先创建新力向量
            self.is_creating_force = True
            self.temp_start_pos = pos
            # 取消所有选中状态
            for force in self.forces:
                force.is_selected = False
            self.selected_force = None
            return
        
        # 检查是否点击了现有的力向量（非中心区域）
        clicked_force = None
        for force in self.forces:
            if force.contains_point(pos):
                # 额外检查：如果力向量的起点在中心区域，只有点击到箭头端点附近才允许拖拽
                force_start_in_center = self._distance(force.start_pos, (center_x, center_y)) <= center_radius
                if force_start_in_center:
                    # 检查是否点击在箭头端点附近（而不是整个向量）
                    if self._distance(pos, force.end_pos) <= 15:
                        clicked_force = force
                        break
                else:
                    # 非中心起点的力向量，正常处理
                    clicked_force = force
                    break
        
        if clicked_force:
            # 选中力向量并开始拖拽
            self.selected_force = clicked_force
            self.dragging_force = True
            # 计算拖拽偏移
            self.drag_offset = (pos[0] - clicked_force.end_pos[0], pos[1] - clicked_force.end_pos[1])
            clicked_force.is_selected = True
        else:
            # 开始创建新的力向量
            self.is_creating_force = True
            self.temp_start_pos = pos
            # 取消所有选中状态
            for force in self.forces:
                force.is_selected = False
            self.selected_force = None
    
    def handle_left_release(self, pos):
        """处理左键释放"""
        if self.is_creating_force and self.temp_start_pos:
            # 完成力向量创建
            if self._distance(self.temp_start_pos, pos) > 10:  # 最小长度限制
                color = self.force_colors[self.color_index % len(self.force_colors)]
                new_force = Force(self.temp_start_pos, pos, color)
                self.forces.append(new_force)
                self.color_index += 1
            
            self.is_creating_force = False
            self.temp_start_pos = None
        
        elif self.dragging_force:
            # 结束拖拽
            self.dragging_force = False
            self.drag_offset = (0, 0)
    
    def handle_right_click(self, pos):
        """处理右键点击（删除力向量）"""
        for i, force in enumerate(self.forces):
            if force.contains_point(pos):
                del self.forces[i]
                self.selected_force = None
                break
    
    def handle_mouse_motion(self, pos):
        """处理鼠标移动"""
        if self.dragging_force and self.selected_force:
            # 拖拽力向量端点
            new_end_pos = (pos[0] - self.drag_offset[0], pos[1] - self.drag_offset[1])
            self.selected_force.end_pos = new_end_pos
    
    def handle_keydown(self, key):
        """处理键盘事件"""
        print(f"键盘事件检测: {pygame.key.name(key)} (代码: {key})")  # 调试输出
        
        if key == pygame.K_c:
            # 清空所有力向量
            self.forces.clear()
            self.selected_force = None
            print("执行: 清空所有力向量")  # 调试输出
        elif key == pygame.K_g:
            # 切换网格显示
            self.show_grid = not self.show_grid
            print(f"执行: 网格显示 {'开启' if self.show_grid else '关闭'}")  # 调试输出
        elif key == pygame.K_h:
            # 切换分量显示
            self.show_components = not self.show_components
            print(f"执行: 分量显示 {'开启' if self.show_components else '关闭'}")  # 调试输出
    
    def update(self):
        """更新仿真状态"""
        # 计算合力
        if self.forces:
            total_x = sum(force.vector.x for force in self.forces)
            total_y = sum(force.vector.y for force in self.forces)
            self.resultant_force = Vector2D(total_x, total_y)
        else:
            self.resultant_force = None
    
    def draw(self):
        """绘制界面"""
        self.screen.fill(self.WHITE)
        
        # 绘制网格
        if self.show_grid:
            self._draw_grid()
          # 绘制坐标轴
        self._draw_axes()
        
        # 绘制中心创建区域指示器
        self._draw_center_zone()
        
        # 绘制所有力向量
        for force in self.forces:
            force.draw(self.screen, self.font)
            
            # 绘制分量（如果开启）
            if self.show_components:
                self._draw_force_components(force)
        
        # 绘制合力
        if self.resultant_force and self.forces:
            self._draw_resultant_force()
        
        # 绘制临时力向量（创建中）
        if self.is_creating_force and self.temp_start_pos:
            mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, self.RED, self.temp_start_pos, mouse_pos, 2)
        
        # 绘制UI面板
        self._draw_ui_panel()
        
        # 绘制帮助信息
        self._draw_help()
        
        pygame.display.flip()
    
    def _draw_grid(self):
        """绘制网格"""
        for x in range(0, self.width, self.grid_size):
            pygame.draw.line(self.screen, self.LIGHT_GRAY, (x, 0), (x, self.height))
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(self.screen, self.LIGHT_GRAY, (0, y), (self.width, y))
    
    def _draw_axes(self):
        """绘制坐标轴"""
        center_x, center_y = self.width // 2, self.height // 2
        
        # X轴
        pygame.draw.line(self.screen, self.BLACK, (50, center_y), (self.width - 50, center_y), 2)
        pygame.draw.polygon(self.screen, self.BLACK, [(self.width - 50, center_y), (self.width - 60, center_y - 5), (self.width - 60, center_y + 5)])
        
        # Y轴
        pygame.draw.line(self.screen, self.BLACK, (center_x, 50), (center_x, self.height - 50), 2)
        pygame.draw.polygon(self.screen, self.BLACK, [(center_x, 50), (center_x - 5, 60), (center_x + 5, 60)])
        
        # 标签
        x_label = self.font.render("X", True, self.BLACK)
        y_label = self.font.render("Y", True, self.BLACK)
        self.screen.blit(x_label, (self.width - 40, center_y + 10))
        self.screen.blit(y_label, (center_x + 10, 30))
    
    def _draw_center_zone(self):
        """绘制中心创建区域指示器"""
        center_x, center_y = self.width // 2, self.height // 2
        center_radius = 30
        
        # 绘制淡色圆圈指示中心区域
        pygame.draw.circle(self.screen, (200, 200, 255, 50), (center_x, center_y), center_radius, 1)
        
        # 在中心绘制一个小十字
        cross_size = 8
        pygame.draw.line(self.screen, self.GRAY, 
                        (center_x - cross_size, center_y), 
                        (center_x + cross_size, center_y), 1)
        pygame.draw.line(self.screen, self.GRAY, 
                        (center_x, center_y - cross_size), 
                        (center_x, center_y + cross_size), 1)
    
    def _draw_force_components(self, force: Force):
        """绘制力的分量"""
        start_x, start_y = force.start_pos
        end_x, end_y = force.end_pos
        
        # X分量（水平）
        if abs(end_x - start_x) > 5:
            pygame.draw.line(self.screen, force.color, (start_x, start_y), (end_x, start_y), 1)
            pygame.draw.line(self.screen, force.color, (end_x, start_y), (end_x, end_y), 1)
    
    def _draw_resultant_force(self):
        """绘制合力"""
        if not self.resultant_force:
            return
        
        # 合力从屏幕中心开始
        center_x, center_y = self.width // 2, self.height // 2
        end_x = center_x + self.resultant_force.x
        end_y = center_y + self.resultant_force.y
        
        # 绘制合力向量（粗线，特殊颜色）
        pygame.draw.line(self.screen, (255, 0, 255), (center_x, center_y), (end_x, end_y), 4)
        
        # 绘制箭头
        if self.resultant_force.magnitude() > 10:
            arrow_length = 20
            arrow_angle = math.pi / 6
            angle = self.resultant_force.angle()
            
            x1 = end_x - arrow_length * math.cos(angle - arrow_angle)
            y1 = end_y - arrow_length * math.sin(angle - arrow_angle)
            x2 = end_x - arrow_length * math.cos(angle + arrow_angle)
            y2 = end_y - arrow_length * math.sin(angle + arrow_angle)
            
            pygame.draw.polygon(self.screen, (255, 0, 255), [(end_x, end_y), (x1, y1), (x2, y2)])
    
    def _draw_ui_panel(self):
        """绘制UI信息面板"""
        panel_x, panel_y = 10, 10
        panel_width = 300
        
        # 背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, 200)
        pygame.draw.rect(self.screen, (255, 255, 255, 200), panel_rect)
        pygame.draw.rect(self.screen, self.BLACK, panel_rect, 2)
        
        y_offset = panel_y + 15
        
        # 标题
        title = self.title_font.render("力的合成仿真", True, self.BLACK)
        self.screen.blit(title, (panel_x + 10, y_offset))
        y_offset += 35
        
        # 力的数量
        count_text = self.font.render(f"力的数量: {len(self.forces)}", True, self.BLACK)
        self.screen.blit(count_text, (panel_x + 10, y_offset))
        y_offset += 25
        
        # 合力信息
        if self.resultant_force:
            mag_text = self.font.render(f"合力大小: {self.resultant_force.magnitude():.2f} N", True, self.BLACK)
            angle_text = self.font.render(f"合力方向: {self.resultant_force.angle_degrees():.1f}°", True, self.BLACK)
            self.screen.blit(mag_text, (panel_x + 10, y_offset))
            y_offset += 20
            self.screen.blit(angle_text, (panel_x + 10, y_offset))
            y_offset += 25
        else:
            no_force_text = self.font.render("无力向量", True, self.GRAY)
            self.screen.blit(no_force_text, (panel_x + 10, y_offset))
            y_offset += 45
        
        # 选中力的信息
        if self.selected_force:
            sel_text = self.font.render("选中力:", True, self.BLACK)
            sel_mag = self.font.render(f"大小: {self.selected_force.magnitude:.2f} N", True, self.BLACK)
            sel_angle = self.font.render(f"角度: {self.selected_force.angle_degrees:.1f}°", True, self.BLACK)
            
            self.screen.blit(sel_text, (panel_x + 10, y_offset))
            y_offset += 20
            self.screen.blit(sel_mag, (panel_x + 10, y_offset))
            y_offset += 15
            self.screen.blit(sel_angle, (panel_x + 10, y_offset))
    
    def _draw_help(self):
        """绘制帮助信息"""
        help_x = self.width - 250
        help_y = 10
        help_texts = [
            "操作说明:",
            "左键拖拽: 创建/移动力向量",
            "中心区域: 优先创建新力向量",
            "右键点击: 删除力向量",
        ]
        
        # 背景
        panel_rect = pygame.Rect(help_x - 10, help_y, 240, len(help_texts) * 20 + 20)
        pygame.draw.rect(self.screen, (255, 255, 255, 200), panel_rect)
        pygame.draw.rect(self.screen, self.BLACK, panel_rect, 1)
        
        # 文本
        for i, text in enumerate(help_texts):
            color = self.BLACK if i == 0 else self.GRAY
            rendered = self.font.render(text, True, color)
            self.screen.blit(rendered, (help_x, help_y + 10 + i * 20))
    
    def _distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """计算两点间距离"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

if __name__ == "__main__":
    simulator = ForceSimulator()
    simulator.run()
