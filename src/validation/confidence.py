# -*- coding: utf-8 -*-
"""
置信度评估器
"""

from typing import Dict, List, Any


class ConfidenceScorer:
    """置信度评分器"""
    
    # 规范参考值
    DESIGN_SPEEDS = [20, 40, 60, 80, 100, 120]
    RADIUS_RANGES = {
        20: (15, 350),
        40: (30, 700),
        60: (60, 1000),
        80: (100, 1500),
        100: (150, 2000),
        120: (200, 3000)
    }
    GRADE_LIMITS = {
        20: 9,    # 90‰
        40: 8,
        60: 7,
        80: 6,
        100: 5,
        120: 4
    }
    
    def __init__(self, design_speed: int = 80):
        self.design_speed = design_speed
        
    def score(self, param_type: str, param_value: Any, context: Dict = None) -> float:
        """评分
        
        Args:
            param_type: 参数类型 (R, A, grade, etc.)
            param_value: 参数值
            context: 上下文
            
        Returns:
            置信度 0-1
        """
        if param_type == "R":
            return self._score_radius(param_value)
        elif param_type == "A":
            return self._score_A(param_value)
        elif param_type in ["grade_in", "grade_out"]:
            return self._score_grade(param_value)
        elif param_type == "elevation":
            return self._score_elevation(param_value)
        elif param_type == "stake":
            return self._score_stake(param_value)
        
        return 0.5  # 默认
    
    def _score_radius(self, R: float) -> float:
        """半径评分"""
        if not R or R <= 0:
            return 0.1
        
        # 检查是否在设计速度对应范围内
        min_r, max_r = self.RADIUS_RANGES.get(self.design_speed, (0, 5000))
        
        if min_r <= R <= max_r:
            # 在范围内，越大越合理
            if R >= min_r * 2:
                return 0.95
            return 0.85
        elif R < min_r:
            return 0.3  # 小于最小值
        else:
            return 0.7  # 超过最大值但可能
        
    def _score_A(self, A: float) -> float:
        """回旋参数评分"""
        if not A or A <= 0:
            return 0.1
        
        # A应该在合理范围
        if 50 <= A <= 2000:
            return 0.9
        elif 20 <= A < 50 or 2000 < A <= 3000:
            return 0.7
        return 0.3
    
    def _score_grade(self, grade: float) -> float:
        """坡度评分"""
        if grade is None:
            return 0.1
        
        grade_abs = abs(grade)
        max_grade = self.GRADE_LIMITS.get(self.design_speed, 10)
        
        if grade_abs <= max_grade:
            if grade_abs <= max_grade * 0.7:
                return 0.95
            return 0.85
        elif grade_abs <= max_grade * 1.2:
            return 0.6
        return 0.2
    
    def _score_elevation(self, elevation: float) -> float:
        """高程评分"""
        if elevation is None or elevation <= 0:
            return 0.1
        
        # 合理范围
        if 0 < elevation < 5000:  # 海拔5km内
            return 0.9
        return 0.5
    
    def _score_stake(self, stake: str) -> float:
        """桩号格式评分"""
        if not stake:
            return 0.1
        
        import re
        if re.match(r'[KZ]?\d+\+\d{3}', stake):
            return 0.95
        elif re.match(r'\d+\+\d{2,3}', stake):
            return 0.8
        return 0.5
    
    def score_params(self, params: Dict) -> Dict:
        """批量评分"""
        scored = {"horizontal_alignment": [], "vertical_alignment": [], "structures": []}
        
        for key in scored.keys():
            for item in params.get(key, []):
                # 基础分数
                base_conf = item.get('confidence', 0.5)
                
                # 各项评分
                scores = []
                if 'R' in item:
                    scores.append(self._score_radius(item['R']))
                if 'A' in item:
                    scores.append(self._score_A(item['A']))
                if 'grade_out' in item:
                    scores.append(self._score_grade(item['grade_out']))
                if 'grade_in' in item:
                    scores.append(self._score_grade(item['grade_in']))
                if 'elevation' in item:
                    scores.append(self._score_elevation(item['elevation']))
                if 'stake' in item:
                    scores.append(self._score_stake(item['stake']))
                
                # 综合评分
                if scores:
                    # 几何平均
                    import math
                    geo_mean = math.exp(sum(math.log(s + 0.01) for s in scores) / len(scores))
                    final_conf = (base_conf + geo_mean) / 2
                else:
                    final_conf = base_conf
                
                item['confidence'] = round(final_conf, 2)
                scored[key].append(item)
        
        return scored


if __name__ == "__main__":
    scorer = ConfidenceScorer(80)
    print(scorer._score_radius(800))  # 应该高
    print(scorer._score_radius(50))   # 应该低
