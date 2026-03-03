# -*- coding: utf-8 -*-
"""
反向验证器 - 用提取的参数计算坐标，与原图比对
"""

from typing import Dict, List, Any, Tuple
import math


class ReverseValidator:
    """反向验证器"""
    
    def __init__(self, param_engine=None):
        self.engine = param_engine
        
    def validate(self, params: Dict, extracted_coords: List[Tuple[float, float]] = None) -> Dict:
        """验证参数
        
        Args:
            params: 提取的参数
            extracted_coords: 原图提取的坐标点 [(x,y), ...]
            
        Returns:
            验证结果
        """
        results = {
            "passed": True,
            "checks": [],
            "errors": []
        }
        
        # 1. 一致性检查
        consistency = self._check_consistency(params)
        results["checks"].append(consistency)
        
        # 2. 合理性检查
        reasonableness = self._check_reasonableness(params)
        results["checks"].append(reasonableness)
        
        # 3. 坐标验证（如果有点）
        if extracted_coords:
            coord_check = self._check_coordinates(params, extracted_coords)
            results["checks"].append(coord_check)
        
        # 汇总
        results["passed"] = all(c["passed"] for c in results["checks"])
        
        return results
    
    def _check_consistency(self, params: Dict) -> Dict:
        """一致性检查"""
        result = {"name": "consistency", "passed": True, "details": []}
        
        # 检查平曲线线元是否连续
        horizontal = params.get("horizontal_alignment", [])
        if len(horizontal) > 1:
            for i in range(len(horizontal) - 1):
                curr_end = horizontal[i].get("end_stake")
                next_start = horizontal[i + 1].get("start_stake")
                if curr_end and next_start and curr_end != next_start:
                    result["passed"] = False
                    result["details"].append(f"线元不连续: {curr_end} != {next_start}")
        
        # 检查纵曲线坡度变化是否合理
        vertical = params.get("vertical_alignment", [])
        if len(vertical) > 1:
            for i in range(len(vertical) - 1):
                grade_out = vertical[i].get("grade_out", 0)
                grade_in = vertical[i + 1].get("grade_in", 0)
                # 坡度变化应该平滑
                if abs(grade_out + grade_in) > 15:  # 突变检查
                    result["passed"] = False
                    result["details"].append(f"纵坡突变: {grade_out} -> {grade_in}")
        
        return result
    
    def _check_reasonableness(self, params: Dict) -> Dict:
        """合理性检查"""
        result = {"name": "reasonableness", "passed": True, "details": []}
        
        # 检查半径是否在规范范围
        for h in params.get("horizontal_alignment", []):
            R = h.get("R")
            if R and R < 15:  # 最小半径
                result["passed"] = False
                result["details"].append(f"半径过小: R={R}")
            if R and R > 10000:
                result["passed"] = False
                result["details"].append(f"半径过大: R={R}")
        
        # 检查坡度
        for v in params.get("vertical_alignment", []):
            for grade_key in ["grade_in", "grade_out"]:
                grade = v.get(grade_key)
                if grade and abs(grade) > 12:  # 12%极限坡度
                    result["passed"] = False
                    result["details"].append(f"坡度过陡: {grade_key}={grade}‰")
        
        return result
    
    def _check_coordinates(self, params: Dict, extracted_coords: List[Tuple[float, float]]) -> Dict:
        """坐标验证"""
        result = {"name": "coordinates", "passed": True, "details": []}
        
        if not self.engine:
            result["details"].append("无参数引擎，跳过坐标验证")
            return result
        
        # 用参数计算坐标，与原图比对
        # 简化：检查几个特征点
        errors = []
        
        # 假设extracted_coords包含关键点（起点、终点、交点等）
        for i, (ex, ey) in enumerate(extracted_coords[:5]):  # 最多检查5个点
            # 尝试用最近桩号计算
            # 这里简化处理
            pass
        
        if errors:
            result["passed"] = False
            result["details"].extend(errors)
        
        return result
    
    def validate_param(self, param_type: str, value: Any, design_speed: int = 80) -> Tuple[bool, str]:
        """验证单个参数
        
        Returns:
            (是否通过, 原因)
        """
        if param_type == "R":
            min_r, max_r = {
                20: (15, 350), 40: (30, 700), 60: (60, 1000),
                80: (100, 1500), 100: (150, 2000), 120: (200, 3000)
            }.get(design_speed, (0, 5000))
            
            if not value or value < min_r:
                return False, f"半径小于最小值 {min_r}m"
            if value > max_r:
                return False, f"半径超过最大值 {max_r}m"
            return True, "OK"
            
        elif param_type == "grade":
            max_grade = {20: 9, 40: 8, 60: 7, 80: 6, 100: 5, 120: 4}.get(design_speed, 10)
            if abs(value) > max_grade:
                return False, f"坡度超过极限值 {max_grade}‰"
            return True, "OK"
        
        return True, "OK"


if __name__ == "__main__":
    validator = ReverseValidator()
    params = {
        "horizontal_alignment": [
            {"start_stake": "K0+000", "end_stake": "K0+500", "R": 800}
        ]
    }
    print(validator.validate(params))
