# -*- coding: utf-8 -*-
"""
测试套件
"""

import unittest
import math
import sys
sys.path.insert(0, '.')

from src.engine.highway_calculator import HighwayCalculator, create_sample_data


class TestHighwayCalculator(unittest.TestCase):
    """计算器测试"""
    
    def setUp(self):
        self.calc = HighwayCalculator()
        self.calc.load_from_json(create_sample_data())
    
    def test_stake_parsing(self):
        """桩号解析"""
        self.assertEqual(self.calc._parse_stake("K0+000"), 0)
        self.assertEqual(self.calc._parse_stake("K1+500"), 1500)
        self.assertEqual(self.calc._parse_stake("K10+000"), 10000)
    
    def test_stake_format(self):
        """桩号格式化"""
        self.assertEqual(self.calc._format_stake(0), "K0+000")
        self.assertEqual(self.calc._format_stake(1500), "K1+500")
        self.assertEqual(self.calc._format_stake(10000), "K10+000")
    
    def test_line_calculation(self):
        """直线计算"""
        x, y, az = self.calc._calc_line(
            type('Obj', (object,), {'x0': 0, 'y0': 0, 'azimuth': 0})(),
            100
        )
        self.assertAlmostEqual(x, 100, places=1)
        self.assertAlmostEqual(y, 0, places=1)
    
    def test_line_45_degree(self):
        """45度直线"""
        elem = type('Obj', (object,), {'x0': 0, 'y0': 0, 'azimuth': 45})()
        x, y, az = self.calc._calc_line(elem, 100)
        # 45度: x = y = 100 * cos(45) = 70.71
        self.assertAlmostEqual(x, 70.71, places=1)
        self.assertAlmostEqual(y, 70.71, places=1)
    
    def test_vertical_no_curve(self):
        """无竖曲线"""
        p = type('Obj', (object,), {
            'stake': 0, 'elevation': 100, 
            'grade_out': 20, 'curve_length': 0
        })()
        z = self.calc._calc_in_vertical(p, 500)
        # z = 100 + 500 * 20/1000 = 110
        self.assertAlmostEqual(z, 110, places=1)
    
    def test_vertical_with_curve(self):
        """有竖曲线"""
        p = type('Obj', (object,), {
            'stake': 0, 'elevation': 100,
            'grade_in': 20, 'grade_out': -20,
            'curve_length': 200
        })()
        z = self.calc._calc_in_vertical(p, 100)
        # 抛物线计算
        self.assertGreater(z, 95)
        self.assertLess(z, 105)
    
    def test_3d_calculation(self):
        """三维计算"""
        result = self.calc.calculate_3d(0)
        self.assertEqual(result['stake'], "K0+000")
        self.assertAlmostEqual(result['z'], 100, places=1)
    
    def test_range_calculation(self):
        """批量计算"""
        results = self.calc.calculate_range(0, 500, 100)
        self.assertEqual(len(results), 6)  # 0,100,200,300,400,500
    
    def test_lod_levels(self):
        """LOD分级"""
        lod0 = self.calc.calculate_lod(0, 100, "LOD0")
        lod1 = self.calc.calculate_lod(0, 100, "LOD1")
        lod2 = self.calc.calculate_lod(0, 100, "LOD2")
        
        self.assertEqual(len(lod0), 3)   # 0,50,100
        self.assertEqual(len(lod1), 11)  # 0,10,20...100
        self.assertEqual(len(lod2), 201)  # 0,0.5,1...100


class TestHorizontalElement(unittest.TestCase):
    """平曲线测试"""
    
    def test_spiral_approximation(self):
        """缓和曲线近似"""
        calc = HighwayCalculator()
        
        elem = type('Obj', (object,), {
            'element_type': '缓和曲线',
            'start_stake': 0, 'end_stake': 100,
            'azimuth': 0, 'x0': 0, 'y0': 0,
            'A': 100, 'direction': '右'
        })()
        
        x, y, az = calc._calc_spiral(elem, 50)
        
        # 简化检查：x应该大于0，y应该大于0
        self.assertGreater(x, 0)
        self.assertGreater(y, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
