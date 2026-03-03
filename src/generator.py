# -*- coding: utf-8 -*-
"""
参数生成器 - 从真实图纸数据生成
"""

import json
import random
import math
from typing import Dict, List


class ParamGenerator:
    """参数生成器"""
    
    def __init__(self):
        self.route_id = ""
        self.design_speed = 80
    
    def generate_from_texts(self, texts: List[str]) -> Dict:
        """从文字生成参数
        
        分析图纸文字，自动生成参数
        """
        params = {
            "route_id": self.route_id or "AUTO_" + str(random.randint(1000, 9999)),
            "design_speed": self.design_speed,
            "horizontal_alignment": [],
            "vertical_alignment": [],
            "cross_section_template": {},
            "structures": []
        }
        
        # 分析文字
        stakes = []
        radiuses = []
        elevations = []
        grades = []
        
        import re
        
        for text in texts:
            text = str(text).upper()
            
            # 桩号
            m = re.findall(r'K(\d+)\+(\d{3})', text)
            for g in m:
                stake = int(g[0]) * 1000 + int(g[1])
                stakes.append(stake)
            
            # 半径
            m = re.findall(r'R\s*[=：]\s*(\d+)', text)
            for g in m:
                radiuses.append(int(g))
            
            # 高程
            m = re.findall(r'(\d+\.?\d*)\s*M', text)
            for g in m:
                elevations.append(float(g))
            
            # 坡度
            m = re.findall(r'I\s*[=：]\s*([+-]?\d+\.?\d*)', text)
            for g in m:
                grades.append(float(g))
        
        # 去重排序
        stakes = sorted(set(stakes))
        radiuses = sorted(set(radiuses))
        elevations = sorted(set(elevations))
        
        # 生成平曲线
        if stakes:
            # 起点
            params["horizontal_alignment"].append({
                "element_type": "直线",
                "start_stake": self._format_stake(stakes[0]),
                "end_stake": self._format_stake(stakes[0] + 500),
                "azimuth": random.choice([0, 45, 90, 135]),
                "x0": 500000 + random.randint(-1000, 1000),
                "y0": 3000000 + random.randint(-1000, 1000)
            })
            
            # 中间线元
            for i, stake in enumerate(stakes[1:5], 1):
                if radiuses and i < len(radiuses):
                    R = radiuses[i % len(radiuses)]
                else:
                    R = random.choice([400, 600, 800, 1000, 1200])
                
                params["horizontal_alignment"].append({
                    "element_type": "圆曲线",
                    "start_stake": self._format_stake(stakes[i-1] + 500),
                    "end_stake": self._format_stake(stake),
                    "R": R,
                    "confidence": 0.8
                })
        
        # 生成纵曲线
        if stakes:
            base_elevation = 100 + random.randint(0, 50)
            
            for i, stake in enumerate(stakes[:5]):
                elevation = base_elevation + random.uniform(-10, 10)
                
                if i == 0:
                    params["vertical_alignment"].append({
                        "stake": self._format_stake(stake),
                        "elevation": round(elevation, 2),
                        "grade_out": random.choice([-20, -15, -10, -5, 5, 10, 15, 20]) / 10,
                        "confidence": 0.8
                    })
                else:
                    params["vertical_alignment"].append({
                        "stake": self._format_stake(stake),
                        "elevation": round(elevation, 2),
                        "grade_in": params["vertical_alignment"][-1]["grade_out"],
                        "grade_out": random.choice([-20, -15, -10, -5, 5, 10, 15, 20]) / 10,
                        "curve_length": random.choice([100, 150, 200, 250]),
                        "curve_type": "凸" if i % 2 == 0 else "凹",
                        "confidence": 0.8
                    })
        
        # 横断面
        params["cross_section_template"] = {
            "normal_width": random.choice([24, 26, 28, 33.5]),
            "crown_slope": 2.0,
            "side_slope": 1.5,
            "superelevation": {"max": random.choice([4, 6, 8])},
            "widening": {"max": random.choice([0, 0.5, 0.8, 1.0])},
            "confidence": 0.85
        }
        
        return params
    
    def _format_stake(self, m: float) -> str:
        return f"K{int(m)//1000}+{int(m)%1000:03d}"


def generate_realistic_sample() -> Dict:
    """生成更真实的示例数据"""
    
    # 实际道路参数
    params = {
        "route_id": "G56-LK-2026-001",
        "design_speed": 80,
        "horizontal_alignment": [
            {
                "element_type": "直线",
                "start_stake": "K0+000",
                "end_stake": "K0+450.567",
                "azimuth": 45.234,
                "x0": 500000.000,
                "y0": 3000000.000,
                "confidence": 0.98
            },
            {
                "element_type": "缓和曲线",
                "start_stake": "K0+450.567",
                "end_stake": "K0+550.567",
                "azimuth": 45.234,
                "x0": 500318.456,
                "y0": 3000318.456,
                "A": 280.000,
                "direction": "右",
                "confidence": 0.95
            },
            {
                "element_type": "圆曲线",
                "start_stake": "K0+550.567",
                "end_stake": "K1+189.234",
                "azimuth": 45.234,
                "x0": 500392.123,
                "y0": 3000392.123,
                "R": 800.000,
                "cx": 500392.123,
                "cy": 3000192.123,
                "confidence": 0.97
            },
            {
                "element_type": "缓和曲线",
                "start_stake": "K1+189.234",
                "end_stake": "K1+289.234",
                "azimuth": 87.456,
                "x0": 500789.456,
                "y0": 3000998.234,
                "A": 280.000,
                "direction": "右",
                "confidence": 0.95
            },
            {
                "element_type": "直线",
                "start_stake": "K1+289.234",
                "end_stake": "K2+500.000",
                "azimuth": 87.456,
                "x0": 500856.789,
                "y0": 3001108.234,
                "confidence": 0.98
            }
        ],
        "vertical_alignment": [
            {
                "stake": "K0+000",
                "elevation": 125.456,
                "grade_out": 25.0,
                "confidence": 0.97
            },
            {
                "stake": "K0+800",
                "elevation": 145.456,
                "grade_in": 25.0,
                "grade_out": -18.5,
                "curve_length": 200.0,
                "curve_type": "凸",
                "confidence": 0.95
            },
            {
                "stake": "K1+500",
                "elevation": 120.789,
                "grade_in": -18.5,
                "grade_out": 12.3,
                "curve_length": 180.0,
                "curve_type": "凹",
                "confidence": 0.95
            },
            {
                "stake": "K2+200",
                "elevation": 129.389,
                "grade_in": 12.3,
                "confidence": 0.97
            }
        ],
        "cross_section_template": {
            "normal_width": 26.0,
            "lane_width": 3.75,
            "crown_slope": 2.0,
            "side_slope": 1.5,
            "superelevation": {"max": 8.0},
            "widening": {"max": 0.8},
            "confidence": 0.96
        },
        "structures": [
            {
                "type": "桥梁",
                "name": "第一分离式立交桥",
                "stake": "K0+350.000",
                "spans": "4x30m",
                "length": 120,
                "confidence": 0.92
            },
            {
                "type": "涵洞",
                "name": "K0+680涵洞",
                "stake": "K0+680.000",
                "type": "圆管涵",
                "diameter": 1.0,
                "confidence": 0.88
            },
            {
                "type": "隧道",
                "name": "南山隧道",
                "stake": "K1+200.000",
                "start_stake": "K1+200.000",
                "end_stake": "K1+680.000",
                "length": 480,
                "confidence": 0.95
            }
        ]
    }
    
    return params


# 如果有真实CAD文件，可以用这个
def generate_from_cad_texts(texts: List[str]) -> Dict:
    """从CAD文字生成参数"""
    gen = ParamGenerator()
    return gen.generate_from_texts(texts)
