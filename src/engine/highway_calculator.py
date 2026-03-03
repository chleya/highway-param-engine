# -*- coding: utf-8 -*-
"""
公路参数计算引擎 - 完整版
支持: 平曲线/纵曲线/横断面计算
"""

import math
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# ========== 数据模型 ==========

@dataclass
class HorizontalElement:
    """平曲线线元"""
    element_type: str      # 直线/缓和曲线/圆曲线
    start_stake: float     # 起点桩号(m)
    end_stake: float       # 终点桩号(m)
    
    # 直线参数
    azimuth: float = 0     # 方位角(度)
    x0: float = 0         # 起点X
    y0: float = 0         # 起点Y
    
    # 圆曲线参数
    R: float = 0          # 半径(m)
    cx: float = 0         # 圆心X
    cy: float = 0         # 圆心Y
    
    # 缓和曲线参数
    A: float = 0          # 回旋参数
    direction: str = "右"   # 左/右
    
    # 切线长
    T1: float = 0         # 前切线长
    T2: float = 0         # 后切线长


@dataclass
class VerticalElement:
    """纵曲线线元"""
    stake: float           # 变坡点桩号(m)
    elevation: float       # 设计高程(m)
    grade_in: float = 0   # 入口坡度(‰)
    grade_out: float = 0   # 出口坡度(‰)
    curve_length: float = 0  # 竖曲线长度(m)
    curve_type: str = "凸"  # 凸/凹


@dataclass
class CrossSection:
    """横断面模板"""
    width: float = 26.0        # 路基宽度(m)
    lane_width: float = 3.75   # 车道宽度
    crown_slope: float = 2.0   # 路拱坡(%)
    side_slope: float = 1.5    # 边坡坡率
    ditch_depth: float = 0.8   # 排水沟深度
    superelevation: float = 0   # 超高(%)
    widening: float = 0        # 加宽(m)


# ========== 核心计算类 ==========

class HighwayCalculator:
    """公路参数计算引擎"""
    
    def __init__(self):
        self.route_id = ""
        self.design_speed = 80  # km/h
        self.horizontal: List[HorizontalElement] = []
        self.vertical: List[VerticalElement] = []
        self.cross_section = CrossSection()
    
    # ========== 加载数据 ==========
    
    def load_from_json(self, data: Dict):
        """从JSON加载"""
        self.route_id = data.get("route_id", "")
        self.design_speed = data.get("design_speed", 80)
        
        # 平曲线
        for h in data.get("horizontal_alignment", []):
            elem = HorizontalElement(
                element_type=h.get("element_type", "直线"),
                start_stake=self._parse_stake(h.get("start_stake", "K0+000")),
                end_stake=self._parse_stake(h.get("end_stake", "K0+000")),
                azimuth=h.get("azimuth", 0),
                x0=h.get("x0", 0),
                y0=h.get("y0", 0),
                R=h.get("R", 0),
                cx=h.get("cx", 0),
                cy=h.get("cy", 0),
                A=h.get("A", 0),
                direction=h.get("direction", "右"),
                T1=h.get("T1", 0),
                T2=h.get("T2", 0)
            )
            self.horizontal.append(elem)
        
        # 纵曲线
        for v in data.get("vertical_alignment", []):
            elem = VerticalElement(
                stake=self._parse_stake(v.get("stake", "K0+000")),
                elevation=v.get("elevation", 0),
                grade_in=v.get("grade_in", 0),
                grade_out=v.get("grade_out", 0),
                curve_length=v.get("curve_length", 0),
                curve_type=v.get("curve_type", "凸")
            )
            self.vertical.append(elem)
        
        # 横断面
        cs = data.get("cross_section_template", {})
        self.cross_section = CrossSection(
            width=cs.get("normal_width", 26.0),
            lane_width=cs.get("lane_width", 3.75),
            crown_slope=cs.get("crown_slope", 2.0),
            side_slope=cs.get("side_slope", 1.5),
            superelevation=cs.get("superelevation", {}).get("max", 0),
            widening=cs.get("widening", {}).get("max", 0)
        )
    
    def _parse_stake(self, s: str) -> float:
        """解析桩号"""
        import re
        m = re.search(r'K?(\d+)\+(\d{3})', str(s).upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0
    
    def _format_stake(self, m: float) -> str:
        """格式化桩号"""
        return f"K{int(m)//1000}+{int(m)%1000:03d}"
    
    # ========== 平曲线计算 ==========
    
    def calculate_horizontal(self, s: float) -> Tuple[float, float, float]:
        """计算平面坐标 (x, y, azimuth)
        
        Args:
            s: 桩号(m)
            
        Returns:
            (x, y, azimuth)
        """
        # 找所在线元
        for elem in self.horizontal:
            if elem.start_stake <= s <= elem.end_stake:
                return self._calc_in_element(elem, s)
        
        # 外推
        if s < self.horizontal[0].start_stake:
            elem = self.horizontal[0]
            ds = s - elem.start_stake
            return self._extrapolate(elem, ds, forward=False)
        else:
            elem = self.horizontal[-1]
            ds = s - elem.start_stake
            return self._extrapolate(elem, ds, forward=True)
    
    def _calc_in_element(self, elem: HorizontalElement, s: float) -> Tuple[float, float, float]:
        """在线元内计算坐标"""
        l = s - elem.start_stake  # 局部里程
        
        if elem.element_type == "直线":
            return self._calc_line(elem, l)
        
        elif elem.element_type == "圆曲线":
            return self._calc_circle(elem, l)
        
        elif elem.element_type == "缓和曲线":
            return self._calc_spiral(elem, l)
        
        return elem.x0, elem.y0, elem.azimuth
    
    def _calc_line(self, elem: HorizontalElement, l: float) -> Tuple[float, float, float]:
        """直线计算
        
        x = x0 + l * cos(α)
        y = y0 + l * sin(α)
        """
        rad = math.radians(elem.azimuth)
        x = elem.x0 + l * math.cos(rad)
        y = elem.y0 + l * math.sin(rad)
        return x, y, elem.azimuth
    
    def _calc_circle(self, elem: HorizontalElement, l: float) -> Tuple[float, float, float]:
        """圆曲线计算
        
        局部坐标系: 以曲线起点为原点，切线方向为X轴
        x = R * sin(θ)
        y = R * (1 - cos(θ))
        θ = l / R
        """
        theta = l / elem.R  # 圆心角
        
        # 起点切线方位角
        start_rad = math.radians(elem.azimuth)
        
        # 局部坐标
        local_x = elem.R * math.sin(theta)
        local_y = elem.R * (1 - math.cos(theta))
        
        # 旋转到真实坐标系
        x = elem.x0 + local_x * math.cos(start_rad) - local_y * math.sin(start_rad)
        y = elem.y0 + local_x * math.sin(start_rad) + local_y * math.cos(start_rad)
        
        # 当前方位角
        azimuth = elem.azimuth + math.degrees(theta)
        
        return x, y, azimuth
    
    def _calc_spiral(self, elem: HorizontalElement, l: float) -> Tuple[float, float, float]:
        """缓和曲线计算 (三次回旋线)
        
        x = l - l^5/(40*R^2*Ls^2) + l^9/(3456*R^4*Ls^4)
        y = l^3/(6*R*Ls) - l^7/(336*R^3*Ls^3) + l^11/(42240*R^5*Ls^5)
        """
        if elem.A == 0:
            elem.A = 1  # 防止除零
        
        # 参数tau
        tau = l * l / (2 * elem.A * elem.A)
        
        # 级数展开
        x = l * (1 - tau**2/10 + tau**4/216 - tau**6/9360)
        y = l * l * l / (6 * elem.A * elem.A) * (1 - tau**2/42 + tau**4/1320)
        
        # 方向判断
        sign = 1 if elem.direction == "右" else -1
        
        # 旋转到真实坐标系
        rad = math.radians(elem.azimuth)
        rx = x * math.cos(rad) - sign * y * math.sin(rad)
        ry = x * math.sin(rad) + sign * y * math.cos(rad)
        
        # 当前方位角近似
        azimuth = elem.azimuth + math.degrees(l / elem.A * elem.A / elem.R) if elem.R else elem.azimuth
        
        return elem.x0 + rx, elem.y0 + ry, azimuth
    
    def _extrapolate(self, elem: HorizontalElement, ds: float, forward: bool) -> Tuple[float, float, float]:
        """外推计算"""
        rad = math.radians(elem.azimuth)
        
        if forward:
            x = elem.x0 + ds * math.cos(rad)
            y = elem.y0 + ds * math.sin(rad)
        else:
            x = elem.x0 - ds * math.cos(rad)
            y = elem.y0 - ds * math.sin(rad)
        
        return x, y, elem.azimuth
    
    # ========== 纵曲线计算 ==========
    
    def calculate_vertical(self, s: float) -> float:
        """计算高程
        
        Args:
            s: 桩号(m)
            
        Returns:
            高程(m)
        """
        if not self.vertical:
            return 0
        
        # 找所在坡段
        for i in range(len(self.vertical) - 1):
            p1 = self.vertical[i]
            p2 = self.vertical[i + 1]
            
            if p1.stake <= s <= p2.stake:
                return self._calc_in_vertical(p1, s)
        
        # 外推
        if s < self.vertical[0].stake:
            p = self.vertical[0]
            ds = s - p.stake
            return p.elevation + ds * p.grade_out / 1000
        else:
            p = self.vertical[-1]
            ds = s - p.stake
            return p.elevation + ds * p.grade_in / 1000
    
    def _calc_in_vertical(self, p: VerticalElement, s: float) -> float:
        """在坡段内计算"""
        l = s - p.stake
        
        # 无竖曲线
        if p.curve_length == 0 or l <= 0:
            return p.elevation + l * p.grade_out / 1000
        
        # 有竖曲线 - 抛物线
        if l <= p.curve_length:
            # 竖曲线段
            grade_diff = p.grade_out - p.grade_in  # ‰
            z = p.elevation + p.grade_in * l / 1000 + grade_diff * l * l / (2 * p.curve_length * 1000)
            return z
        else:
            # 超出竖曲线段
            l2 = l - p.curve_length
            return p.elevation + p.grade_out * p.curve_length / 1000 + p.grade_out * l2 / 1000
    
    # ========== 组合计算 ==========
    
    def calculate_3d(self, s: float) -> Dict:
        """计算三维坐标
        
        Args:
            s: 桩号(m)
            
        Returns:
            {stake, x, y, z, azimuth}
        """
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
        """批量计算
        
        Args:
            start: 起始桩号(m)
            end: 结束桩号(m)
            interval: 间隔(m)
            
        Returns:
            三维坐标列表
        """
        results = []
        s = start
        while s <= end:
            results.append(self.calculate_3d(s))
            s += interval
        return results
    
    # ========== LOD计算 ==========
    
    def calculate_lod(self, start: float, end: float, lod: str) -> List[Dict]:
        """LOD计算
        
        LOD0: 50m间隔 (米级)
        LOD1: 10m间隔 (分米级)
        LOD2: 0.5m间隔 (厘米级)
        """
        intervals = {"LOD0": 50, "LOD1": 10, "LOD2": 0.5}
        interval = intervals.get(lod, 50)
        return self.calculate_range(start, end, interval)
    
    # ========== 横断面计算 ==========
    
    def calculate_cross_section(self, s: float, offset: float = 0) -> Dict:
        """计算横断面
        
        Args:
            s: 桩号(m)
            offset: 横向偏移(m), 左负右正
            
        Returns:
            横断面点坐标
        """
        # 中心点
        cx, cy, azimuth = self.calculate_horizontal(s)
        cz = self.calculate_vertical(s)
        
        # 横断参数
        half_width = self.cross_section.width / 2
        crown = self.cross_section.crown_slope / 100 * half_width
        
        # 超高旋转
        super_elev = self.cross_section.superelevation
        
        # 计算左中右点
        rad = math.radians(azimuth)
        
        # 中心
        center = {"x": cx, "y": cy, "z": cz}
        
        # 左侧
        left_x = cx + (half_width + offset) * math.cos(rad + math.pi/2)
        left_y = cy + (half_width + offset) * math.sin(rad + math.pi/2)
        left_z = cz - crown + (half_width + offset) * math.tan(math.radians(super_elev))
        
        # 右侧
        right_x = cx + (half_width - offset) * math.cos(rad - math.pi/2)
        right_y = cy + (half_width - offset) * math.sin(rad - math.pi/2)
        right_z = cz + crown - (half_width - offset) * math.tan(math.radians(super_elev))
        
        return {
            "stake": self._format_stake(s),
            "center": center,
            "left": {"x": round(left_x, 3), "y": round(left_y, 3), "z": round(left_z, 3)},
            "right": {"x": round(right_x, 3), "y": round(right_y, 3), "z": round(right_z, 3)},
            "width": self.cross_section.width,
            "superelevation": super_elev
        }
    
    # ========== 工具函数 ==========
    
    def get_stake_range(self) -> Tuple[float, float]:
        """获取桩号范围"""
        if not self.horizontal:
            return 0, 0
        return self.horizontal[0].start_stake, self.horizontal[-1].end_stake
    
    def get_element_at(self, s: float) -> Optional[HorizontalElement]:
        """获取指定桩号所在的线元"""
        for elem in self.horizontal:
            if elem.start_stake <= s <= elem.end_stake:
                return elem
        return None


# ========== 示例数据 ==========

def create_sample_data() -> Dict:
    """创建示例数据"""
    return {
        "route_id": "LK-2026-001",
        "design_speed": 80,
        "horizontal_alignment": [
            {
                "element_type": "直线",
                "start_stake": "K0+000",
                "end_stake": "K0+500",
                "azimuth": 45.0,
                "x0": 500000,
                "y0": 3000000
            },
            {
                "element_type": "缓和曲线",
                "start_stake": "K0+500",
                "end_stake": "K0+600",
                "azimuth": 45.0,
                "x0": 500353.553,
                "y0": 3000353.553,
                "A": 300,
                "direction": "右"
            },
            {
                "element_type": "圆曲线",
                "start_stake": "K0+600",
                "end_stake": "K1+200",
                "azimuth": 45.0,
                "x0": 500424.264,
                "y0": 3000424.264,
                "R": 800,
                "cx": 500424.264,
                "cy": 3000224.264
            },
            {
                "element_type": "缓和曲线",
                "start_stake": "K1+200",
                "end_stake": "K1+300",
                "azimuth": 90.0,
                "x0": 500777.911,
                "y0": 3000997.911,
                "A": 300,
                "direction": "右"
            },
            {
                "element_type": "直线",
                "start_stake": "K1+300",
                "end_stake": "K2+000",
                "azimuth": 90.0,
                "x0": 500848.853,
                "y0": 3001097.911
            }
        ],
        "vertical_alignment": [
            {
                "stake": "K0+000",
                "elevation": 100.0,
                "grade_out": 20.0
            },
            {
                "stake": "K0+500",
                "elevation": 110.0,
                "grade_in": 20.0,
                "grade_out": -15.0,
                "curve_length": 200,
                "curve_type": "凸"
            },
            {
                "stake": "K1+200",
                "elevation": 99.5,
                "grade_in": -15.0,
                "grade_out": 10.0,
                "curve_length": 150,
                "curve_type": "凹"
            },
            {
                "stake": "K2+000",
                "elevation": 108.0,
                "grade_in": 10.0
            }
        ],
        "cross_section_template": {
            "normal_width": 26.0,
            "crown_slope": 2.0,
            "side_slope": 1.5,
            "superelevation": {"max": 8.0},
            "widening": {"max": 0.8}
        }
    }


# ========== 主程序 ==========

if __name__ == "__main__":
    # 创建计算器
    calc = HighwayCalculator()
    
    # 加载示例数据
    sample = create_sample_data()
    calc.load_from_json(sample)
    
    print("=== Highway Calculator Test ===\n")
    
    # 测试点
    test_stakes = [0, 100, 250, 500, 600, 800, 1000, 1200, 1500, 2000]
    
    for s in test_stakes:
        result = calc.calculate_3d(s)
        print(f"{result['stake']}: X={result['x']} Y={result['y']} Z={result['z']} 方位={result['azimuth']}°")
    
    print("\n=== LOD0 Sample (50m) ===")
    lod0 = calc.calculate_lod(0, 1000, "LOD0")
    for p in lod0:
        print(f"{p['stake']}: ({p['x']}, {p['y']}, {p['z']})")
    
    print("\n=== Cross Section at K0+500 ===")
    cs = calc.calculate_cross_section(500)
    print(f"Center: ({cs['center']['x']}, {cs['center']['y']}, {cs['center']['z']})")
    print(f"Left: ({cs['left']['x']}, {cs['left']['y']}, {cs['left']['z']})")
    print(f"Right: ({cs['right']['x']}, {cs['right']['y']}, {cs['right']['z']})")
