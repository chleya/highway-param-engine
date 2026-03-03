# -*- coding: utf-8 -*-
"""
公路参数计算引擎
"""

import math
import re
from typing import Dict, List, Tuple, Optional


class HighwayEngine:
    """公路参数计算引擎"""
    
    def __init__(self):
        self.route_id = ""
        self.design_speed = 80
        self.horizontal = []  # 平曲线线元
        self.vertical = []    # 纵曲线线元
        self.cross_section = {}  # 横断面模板
        
    def load_from_params(self, params: Dict):
        """从参数字典加载"""
        self.route_id = params.get('route_id', '')
        self.design_speed = params.get('design_speed', 80)
        
        # 加载平曲线
        for h in params.get('horizontal_alignment', []):
            self.horizontal.append(HorizontalElement(h))
        
        # 加载纵曲线
        for v in params.get('vertical_alignment', []):
            self.vertical.append(VerticalElement(v))
        
        # 加载横断面
        self.cross_section = params.get('cross_section_template', {})
    
    def calculate_horizontal(self, s: float) -> Tuple[float, float, float]:
        """计算平面坐标 (x, y, azimuth)"""
        if not self.horizontal:
            return 0, 0, 0
        
        # 找所在线元
        for elem in self.horizontal:
            if elem.start_stake <= s <= elem.end_stake:
                return elem.calculate(s)
        
        # 外推
        if s < self.horizontal[0].start_stake:
            elem = self.horizontal[0]
            ds = s - elem.start_stake
            return elem.extrapolate_before(ds)
        else:
            elem = self.horizontal[-1]
            ds = s - elem.start_stake
            return elem.extrapolate_after(ds)
    
    def calculate_vertical(self, s: float) -> float:
        """计算高程"""
        if not self.vertical:
            return 0
        
        # 找所在坡段
        for i in range(len(self.vertical) - 1):
            p1 = self.vertical[i]
            p2 = self.vertical[i + 1]
            
            if p1.stake <= s <= p2.stake:
                return p1.calculate(s)
        
        # 外推
        if s < self.vertical[0].stake:
            p = self.vertical[0]
            ds = s - p.stake
            return p.elevation + ds * p.grade_out / 1000
        else:
            p = self.vertical[-1]
            ds = s - p.stake
            return p.elevation + ds * p.grade_in / 1000
    
    def calculate_3d(self, s: float) -> Dict:
        """计算三维坐标"""
        x, y, azimuth = self.calculate_horizontal(s)
        z = self.calculate_vertical(s)
        
        return {
            "stake": self._format_stake(s),
            "stake_m": s,
            "x": round(x, 3),
            "y": round(y, 3),
            "z": round(z, 3),
            "azimuth": round(azimuth, 3)
        }
    
    def calculate_range(self, start: float, end: float, interval: float = 100) -> List[Dict]:
        """批量计算"""
        results = []
        s = start
        while s <= end:
            results.append(self.calculate_3d(s))
            s += interval
        return results
    
    def calculate_lod(self, start: float, end: float, lod_level: str) -> List[Dict]:
        """LOD计算"""
        intervals = {
            "LOD0": 50,
            "LOD1": 10,
            "LOD2": 0.5
        }
        interval = intervals.get(lod_level, 50)
        return self.calculate_range(start, end, interval)
    
    def calculate_cross_section(self, s: float, offset: float = 0) -> Dict:
        """计算横断面"""
        x, y, azimuth = self.calculate_horizontal(s)
        z = self.calculate_vertical(s)
        
        width = self.cross_section.get('normal_width', 26) / 2
        
        # 计算左右点
        left_az = azimuth + 90
        right_az = azimuth - 90
        
        left_x = x + width * math.cos(math.radians(left_az))
        left_y = y + width * math.sin(math.radians(left_az))
        
        right_x = x + width * math.cos(math.radians(right_az))
        right_y = y + width * math.sin(math.radians(right_az))
        
        return {
            "center": {"x": x, "y": y, "z": z},
            "left": {"x": left_x, "y": left_y, "z": z},
            "right": {"x": right_x, "y": right_y, "z": z},
            "width": width * 2
        }
    
    def _format_stake(self, s: float) -> str:
        """格式化桩号"""
        return f"K{s//1000}+{s%1000:03d}"
    
    def _parse_stake(self, stake_str: str) -> float:
        """解析桩号"""
        m = re.search(r'K?(\d+)\+(\d{3})', stake_str.upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0


class HorizontalElement:
    """平曲线线元"""
    
    def __init__(self, data: Dict):
        self.element_type = data.get('element_type', '直线')
        self.start_stake = self._parse_stake(data.get('start_stake', 'K0+000'))
        self.end_stake = self._parse_stake(data.get('end_stake', 'K0+000'))
        
        # 直线参数
        self.azimuth = data.get('azimuth', 0)
        self.x0 = data.get('x0', 0)
        self.y0 = data.get('y0', 0)
        
        # 圆曲线参数
        self.R = data.get('R', 0)
        self.cx = data.get('cx', 0)
        self.cy = data.get('cy', 0)
        
        # 缓和曲线参数
        self.A = data.get('A', 0)
        self.direction = data.get('direction', '右')
    
    def _parse_stake(self, s: str) -> float:
        m = re.search(r'K?(\d+)\+(\d{3})', str(s).upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0
    
    def calculate(self, s: float) -> Tuple[float, float, float]:
        """计算坐标"""
        l = s - self.start_stake
        
        if self.element_type == '直线':
            x = self.x0 + l * math.cos(math.radians(self.azimuth))
            y = self.y0 + l * math.sin(math.radians(self.azimuth))
            return x, y, self.azimuth
        
        elif self.element_type == '圆曲线':
            theta = l / self.R
            start_a = math.radians(self.azimuth)
            current_a = start_a + theta
            x = self.cx + self.R * math.cos(current_a)
            y = self.cy + self.R * math.sin(current_a)
            return x, y, math.degrees(current_a)
        
        elif self.element_type == '缓和曲线':
            tau = l * l / (2 * self.A * self.A)
            x = l * (1 - tau * tau / 10)
            y = l * l * l / (6 * self.A * self.A)
            rad = math.radians(self.azimuth)
            rx = x * math.cos(rad) - y * math.sin(rad)
            ry = x * math.sin(rad) + y * math.cos(rad)
            return self.x0 + rx, self.y0 + ry, self.azimuth
        
        return self.x0, self.y0, self.azimuth
    
    def extrapolate_before(self, ds: float) -> Tuple[float, float, float]:
        """向前外推"""
        x = self.x0 - ds * math.cos(math.radians(self.azimuth))
        y = self.y0 - ds * math.sin(math.radians(self.azimuth))
        return x, y, self.azimuth
    
    def extrapolate_after(self, ds: float) -> Tuple[float, float, float]:
        """向后外推"""
        x = self.x0 + ds * math.cos(math.radians(self.azimuth))
        y = self.y0 + ds * math.sin(math.radians(self.azimuth))
        return x, y, self.azimuth


class VerticalElement:
    """纵曲线线元"""
    
    def __init__(self, data: Dict):
        self.stake = self._parse_stake(data.get('stake', 'K0+000'))
        self.elevation = data.get('elevation', 0)
        self.grade_in = data.get('grade_in', 0)
        self.grade_out = data.get('grade_out', 0)
        self.curve_length = data.get('curve_length', 0)
        self.curve_type = data.get('curve_type', '凸')
    
    def _parse_stake(self, s: str) -> float:
        m = re.search(r'K?(\d+)\+(\d{3})', str(s).upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0
    
    def calculate(self, s: float) -> float:
        """计算高程"""
        l = s - self.stake
        
        if self.curve_length == 0:
            return self.elevation + l * self.grade_out / 1000
        
        # 抛物线竖曲线
        grade_diff = self.grade_out - self.grade_in
        z = self.elevation + self.grade_in * l / 1000 + grade_diff * l * l / (2 * self.curve_length * 1000)
        return z


class LODManager:
    """LOD管理器"""
    
    @staticmethod
    def get_interval(lod_level: str) -> float:
        """获取LOD间隔"""
        return {
            "LOD0": 50,
            "LOD1": 10,
            "LOD2": 0.5
        }.get(lod_level, 50)
    
    @staticmethod
    def should_upgrade(current_lod: str, error_threshold: float) -> bool:
        """判断是否需要升级LOD"""
        if current_lod == "LOD0" and error_threshold > 0.5:
            return True
        elif current_lod == "LOD1" and error_threshold > 0.05:
            return True
        return False


if __name__ == "__main__":
    engine = HighwayEngine()
    params = {
        "route_id": "LK-2026-001",
        "design_speed": 80,
        "horizontal_alignment": [
            {"element_type": "直线", "start_stake": "K0+000", "end_stake": "K0+500",
             "azimuth": 45, "x0": 500000, "y0": 3000000}
        ],
        "vertical_alignment": [
            {"stake": "K0+000", "elevation": 100, "grade_out": 20}
        ]
    }
    engine.load_from_params(params)
    print(engine.calculate_3d(250))
