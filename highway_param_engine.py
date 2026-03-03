# -*- coding: utf-8 -*-
"""
公路参数化计算引擎 V1.0
"""

import math
import json
import re
from typing import Dict, List, Tuple


class HorizontalElement:
    """平曲线线元"""
    def __init__(self, data: Dict):
        self.element_type = data.get("element_type", "直线")
        self.start_stake = self._parse_stake(data.get("start_stake", "K0+000"))
        self.end_stake = self._parse_stake(data.get("end_stake", "K0+000"))
        self.azimuth = data.get("azimuth", 0)
        self.x0 = data.get("x0", 0)
        self.y0 = data.get("y0", 0)
        self.R = data.get("R", 0)
        self.cx = data.get("cx", 0)
        self.cy = data.get("cy", 0)
        self.A = data.get("A", 0)
        self.direction = data.get("direction", "右")
        self.confidence = data.get("confidence", 1.0)
        
        # 圆曲线参数
        if "start_angle" in data:
            self.start_angle = data.get("start_angle", 0)
    
    def _parse_stake(self, s: str) -> float:
        m = re.search(r'K?(\d+)\+(\d{3})', s.upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0


class VerticalElement:
    """纵曲线线元"""
    def __init__(self, data: Dict):
        self.stake = self._parse_stake(data.get("stake", "K0+000"))
        self.elevation = data.get("elevation", 0)
        self.grade_in = data.get("grade_in", 0)
        self.grade_out = data.get("grade_out", 0)
        self.curve_length = data.get("curve_length", 0)
        self.curve_type = data.get("curve_type", "凸")
        self.confidence = data.get("confidence", 1.0)
    
    def _parse_stake(self, s: str) -> float:
        m = re.search(r'K?(\d+)\+(\d{3})', s.upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0


class CrossSectionTemplate:
    """横断面模板"""
    def __init__(self, data: Dict = None):
        if data:
            self.normal_width = data.get("normal_width", 26.0)
            self.crown_slope = data.get("crown_slope", 2.0)
            self.side_slope = data.get("side_slope", 1.5)
            self.superelevation_max = data.get("superelevation_max", 8.0)
            self.widening_max = data.get("widening_max", 0.8)
        else:
            self.normal_width = 26.0
            self.crown_slope = 2.0
            self.side_slope = 1.5
            self.superelevation_max = 8.0
            self.widening_max = 0.8


class HighwayParamEngine:
    """公路参数化计算引擎"""
    
    def __init__(self):
        self.route_id = ""
        self.design_speed = 80
        self.horizontal = []
        self.vertical = []
        self.cross_section = CrossSectionTemplate()
    
    def load_from_json(self, data: Dict):
        """从JSON加载"""
        self.route_id = data.get("route_id", "")
        self.design_speed = data.get("design_speed", 80)
        
        for h in data.get("horizontal_alignment", []):
            self.horizontal.append(HorizontalElement(h))
        
        for v in data.get("vertical_alignment", []):
            self.vertical.append(VerticalElement(v))
        
        cs_data = data.get("cross_section_template", {})
        self.cross_section = CrossSectionTemplate(cs_data)
    
    def _parse_stake(self, s: str) -> float:
        m = re.search(r'K?(\d+)\+(\d{3})', s.upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0
    
    def calculate_horizontal(self, s: float) -> Tuple[float, float, float]:
        """计算平面坐标 (x, y, azimuth)"""
        for elem in self.horizontal:
            if elem.start_stake <= s <= elem.end_stake:
                return self._calc_in_elem(elem, s)
        
        # 外推
        if s < self.horizontal[0].start_stake:
            elem = self.horizontal[0]
            ds = s - elem.start_stake
            return (
                elem.x0 + ds * math.cos(math.radians(elem.azimuth)),
                elem.y0 + ds * math.sin(math.radians(elem.azimuth)),
                elem.azimuth
            )
        else:
            elem = self.horizontal[-1]
            ds = s - elem.start_stake
            return (
                elem.x0 + ds * math.cos(math.radians(elem.azimuth)),
                elem.y0 + ds * math.sin(math.radians(elem.azimuth)),
                elem.azimuth
            )
    
    def _calc_in_elem(self, elem: HorizontalElement, s: float) -> Tuple[float, float, float]:
        """在线元内计算"""
        l = s - elem.start_stake
        
        if elem.element_type == "直线":
            x = elem.x0 + l * math.cos(math.radians(elem.azimuth))
            y = elem.y0 + l * math.sin(math.radians(elem.azimuth))
            return x, y, elem.azimuth
        
        elif elem.element_type == "圆曲线":
            theta = l / elem.R
            start_a = math.radians(getattr(elem, 'start_angle', 45))
            current_a = start_a + theta
            x = elem.cx + elem.R * math.cos(current_a)
            y = elem.cy + elem.R * math.sin(current_a)
            return x, y, math.degrees(current_a)
        
        elif elem.element_type == "缓和曲线":
            tau = l * l / (2 * elem.A * elem.A)
            x = l * (1 - tau * tau / 10)
            y = l * l * l / (6 * elem.A * elem.A)
            rad = math.radians(elem.azimuth)
            rx = x * math.cos(rad) - y * math.sin(rad)
            ry = x * math.sin(rad) + y * math.cos(rad)
            return elem.x0 + rx, elem.y0 + ry, elem.azimuth
        
        return elem.x0, elem.y0, elem.azimuth
    
    def calculate_vertical(self, s: float) -> float:
        """计算高程"""
        if not self.vertical:
            return 0
        
        for i in range(len(self.vertical) - 1):
            p1 = self.vertical[i]
            p2 = self.vertical[i + 1]
            if p1.stake <= s <= p2.stake:
                l = s - p1.stake
                length = p2.stake - p1.stake
                if p1.curve_length == 0:
                    return p1.elevation + l * p1.grade_out / 1000
                else:
                    grade_diff = p1.grade_out - p1.grade_in
                    return p1.elevation + p1.grade_in * l / 1000 + grade_diff * l * l / (2 * p1.curve_length * 1000)
        
        # 外推
        if s < self.vertical[0].stake:
            p = self.vertical[0]
            return p.elevation + (s - p.stake) * p.grade_in / 1000
        else:
            p = self.vertical[-1]
            return p.elevation + (s - p.stake) * p.grade_out / 1000
    
    def calculate_3d(self, s: float) -> Dict:
        """计算三维坐标"""
        x, y, azimuth = self.calculate_horizontal(s)
        z = self.calculate_vertical(s)
        return {
            "stake": f"K{s//1000}+{s%1000:03d}",
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


# 示例
if __name__ == "__main__":
    engine = HighwayParamEngine()
    
    sample = {
        "route_id": "LK-2026-001",
        "horizontal_alignment": [
            {"element_type": "直线", "start_stake": "K0+000", "end_stake": "K0+500",
             "azimuth": 45, "x0": 500000, "y0": 3000000, "confidence": 0.99},
            {"element_type": "圆曲线", "start_stake": "K0+500", "end_stake": "K0+800",
             "R": 800, "cx": 500212, "cy": 3000212, "start_angle": 45, "confidence": 0.99}
        ],
        "vertical_alignment": [
            {"stake": "K0+000", "elevation": 100, "grade_out": 20, "confidence": 0.97},
            {"stake": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "curve_length": 200, "confidence": 0.97}
        ]
    }
    
    engine.load_from_json(sample)
    
    print("=== 参数化引擎测试 ===\n")
    for s in [0, 100, 250, 500, 600, 800]:
        r = engine.calculate_3d(s)
        print(f"{r['stake']}: X={r['x']} Y={r['y']} Z={r['z']} 方位={r['azimuth']}°")
