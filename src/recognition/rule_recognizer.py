# -*- coding: utf-8 -*-
"""
规则引擎 - 正则快速匹配
"""

import re
from typing import Dict, List, Any, Tuple


class RuleRecognizer:
    """规则引擎"""
    
    # 桩号正则
    STAKE_PATTERN = re.compile(r'(ZK|YK|K)\+(\d{3})')
    
    # 参数正则
    RADIUS_PATTERN = re.compile(r'R\s*[=：:]?\s*(\d+\.?\d*)', re.IGNORECASE)
    A_PATTERN = re.compile(r'A\s*[=：:]?\s*(\d+\.?\d*)', re.IGNORECASE)
    LS_PATTERN = re.compile(r'Ls?\s*[=：:]?\s*(\d+\.?\d*)', re.IGNORECASE)
    GRADE_PATTERN = re.compile(r'i\s*[=：:]?\s*([+-]?\d+\.?\d*)\s*[%‰]?', re.IGNORECASE)
    ELEVATION_PATTERN = re.compile(r'高程[=：:]?\s*(\d+\.?\d*)', re.IGNORECASE)
    LENGTH_PATTERN = re.compile(r'L\s*[=：:]?\s*(\d+\.?\d*)\s*m?', re.IGNORECASE)
    SPANS_PATTERN = re.compile(r'(\d+)\s*[×x]\s*(\d+)\s*m?', re.IGNORECASE)
    DIAMETER_PATTERN = re.compile(r'φ\s*(\d+\.?\d*)\s*m?', re.IGNORECASE)
    WIDTH_PATTERN = re.compile(r'宽\s*[=：:]?\s*(\d+\.?\d*)\s*m?', re.IGNORECASE)
    
    def __init__(self):
        self.rules = self._init_rules()
        
    def _init_rules(self) -> Dict:
        """初始化规则"""
        return {
            "bridge": {
                "keywords": ["桥", "bridge"],
                "patterns": [self.STAKE_PATTERN, self.SPANS_PATTERN],
                "type": "桥梁"
            },
            "culvert": {
                "keywords": ["涵", "涵洞", "culvert"],
                "patterns": [self.STAKE_PATTERN, self.DIAMETER_PATTERN],
                "type": "涵洞"
            },
            "tunnel": {
                "keywords": ["隧道", "洞", "tunnel"],
                "patterns": [self.STAKE_PATTERN, self.LENGTH_PATTERN],
                "type": "隧道"
            },
            "horizontal": {
                "keywords": ["JD", "交点", "偏角", "半径"],
                "patterns": [self.STAKE_PATTERN, self.RADIUS_PATTERN, self.A_PATTERN, self.LS_PATTERN],
                "type": "平曲线"
            },
            "vertical": {
                "keywords": ["变坡", "纵坡", "坡度", "高程"],
                "patterns": [self.STAKE_PATTERN, self.ELEVATION_PATTERN, self.GRADE_PATTERN],
                "type": "纵曲线"
            }
        }
    
    def recognize(self, texts: List[str]) -> Dict:
        """识别参数"""
        results = {
            "horizontal_alignment": [],
            "vertical_alignment": [],
            "structures": []
        }
        
        seen_stakes = set()
        
        for text in texts:
            text = str(text).upper()
            
            # 检测类型
            detected_type = self._detect_type(text)
            
            if detected_type == "平曲线":
                params = self._extract_horizontal(text)
                if params and params.get('stake'):
                    stake = params['stake']
                    if stake not in seen_stakes:
                        seen_stakes.add(stake)
                        params['confidence'] = 0.9
                        params['source'] = 'rule'
                        results["horizontal_alignment"].append(params)
                        
            elif detected_type == "纵曲线":
                params = self._extract_vertical(text)
                if params and params.get('stake'):
                    stake = params['stake']
                    if stake not in seen_stakes:
                        seen_stakes.add(stake)
                        params['confidence'] = 0.9
                        params['source'] = 'rule'
                        results["vertical_alignment"].append(params)
                        
            elif detected_type in ["桥梁", "涵洞", "隧道"]:
                params = self._extract_structure(text, detected_type)
                if params and params.get('stake'):
                    stake = params['stake']
                    if stake not in seen_stakes:
                        seen_stakes.add(stake)
                        params['confidence'] = 0.9
                        params['source'] = 'rule'
                        results["structures"].append(params)
        
        return results
    
    def _detect_type(self, text: str) -> str:
        """检测参数类型"""
        for rule_name, rule in self.rules.items():
            if any(kw in text for kw in rule["keywords"]):
                return rule["type"]
        return "unknown"
    
    def _extract_horizontal(self, text: str) -> Dict:
        """提取平曲线参数"""
        result = {"element_type": "圆曲线"}
        
        # 桩号
        m = self.STAKE_PATTERN.search(text)
        if m:
            prefix = m.group(1) or 'K'
            result["stake"] = f"{prefix}+{m.group(2)}"
            result["start_stake"] = result["stake"]
            
        # 半径
        m = self.RADIUS_PATTERN.search(text)
        if m:
            result["R"] = float(m.group(1))
            
        # 回旋参数
        m = self.A_PATTERN.search(text)
        if m:
            result["A"] = float(m.group(1))
            
        # 缓和长度
        m = self.LS_PATTERN.search(text)
        if m:
            result["Ls"] = float(m.group(1))
        
        return result if "R" in result or "A" in result else None
    
    def _extract_vertical(self, text: str) -> Dict:
        """提取纵曲线参数"""
        result = {}
        
        # 桩号
        m = self.STAKE_PATTERN.search(text)
        if m:
            prefix = m.group(1) or 'K'
            result["stake"] = f"{prefix}+{m.group(2)}"
            
        # 高程
        m = self.ELEVATION_PATTERN.search(text)
        if m:
            result["elevation"] = float(m.group(1))
            
        # 坡度
        grades = self.GRADE_PATTERN.findall(text)
        if grades:
            if len(grades) >= 1:
                result["grade_out"] = float(grades[0])
            if len(grades) >= 2:
                result["grade_in"] = float(grades[1])
                
        return result if result.get("stake") else None
    
    def _extract_structure(self, text: str, struct_type: str) -> Dict:
        """提取结构物参数"""
        result = {"type": struct_type}
        
        # 桩号
        m = self.STAKE_PATTERN.search(text)
        if m:
            prefix = m.group(1) or 'K'
            result["stake"] = f"{prefix}+{m.group(2)}"
        
        # 桥梁跨径
        if struct_type == "桥梁":
            m = self.SPANS_PATTERN.search(text)
            if m:
                result["spans"] = f"{m.group(1)}x{m.group(2)}m"
                
        # 涵洞直径
        elif struct_type == "涵洞":
            m = self.DIAMETER_PATTERN.search(text)
            if m:
                result["diameter"] = f"φ{m.group(1)}m"
                
        # 隧道长度
        elif struct_type == "隧道":
            m = self.LENGTH_PATTERN.search(text)
            if m:
                result["length"] = f"{m.group(1)}m"
        
        return result if result.get("stake") else None


if __name__ == "__main__":
    recognizer = RuleRecognizer()
    test_texts = [
        "K4+456 七铁塘桥 8x30m",
        "JD3 R=800 A=300 Ls=100",
        "K0+800 高程=125.45 i1=20‰ i2=-15‰"
    ]
    result = recognizer.recognize(test_texts)
    print(result)
