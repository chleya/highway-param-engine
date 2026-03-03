# -*- coding: utf-8 -*-
"""
统一识别接口
"""

from typing import Dict, List, Any
from .llm_recognizer import LLMRecognizer
from .rule_recognizer import RuleRecognizer


class UnifiedRecognizer:
    """统一识别器 - LLM + 规则双通道"""
    
    def __init__(self):
        self.llm = LLMRecognizer()
        self.rule = RuleRecognizer()
        
    def recognize(self, texts: List[str], tables: List[List] = None, 
                  use_llm: bool = True, use_rule: bool = True) -> Dict:
        """识别参数
        
        Args:
            texts: 文字列表
            tables: 表格列表
            use_llm: 使用LLM识别
            use_rule: 使用规则识别
            
        Returns:
            合并后的参数
        """
        results = {
            "horizontal_alignment": [],
            "vertical_alignment": [],
            "structures": []
        }
        
        # 规则识别（快速通道）
        if use_rule:
            rule_results = self.rule.recognize(texts)
            results = self._merge(results, rule_results, source="rule")
        
        # LLM识别（深度理解）
        if use_llm:
            llm_results = self.llm.recognize(texts)
            results = self._merge(results, llm_results, source="llm")
            
            # 表格识别
            if tables:
                for table in tables:
                    table_results = self.llm.recognize_table(table)
                    results = self._merge(results, table_results, source="llm_table")
        
        # 去重合并
        results = self._deduplicate(results)
        
        # 计算综合置信度
        results = self._calc_confidence(results)
        
        return results
    
    def _merge(self, base: Dict, new: Dict, source: str) -> Dict:
        """合并结果"""
        for key in ["horizontal_alignment", "vertical_alignment", "structures"]:
            if key in new and isinstance(new[key], list):
                for item in new[key]:
                    item['source'] = source
                    base[key].append(item)
        return base
    
    def _deduplicate(self, results: Dict) -> Dict:
        """去重"""
        for key in ["horizontal_alignment", "vertical_alignment", "structures"]:
            seen = set()
            deduped = []
            
            for item in results.get(key, []):
                # 用stake作为唯一标识
                stake = item.get('stake') or item.get('start_stake')
                if stake and stake not in seen:
                    seen.add(stake)
                    deduped.append(item)
                elif not stake:
                    deduped.append(item)
            
            results[key] = deduped
        
        return results
    
    def _calc_confidence(self, results: Dict) -> Dict:
        """计算综合置信度"""
        for key in ["horizontal_alignment", "vertical_alignment", "structures"]:
            for item in results.get(key, []):
                conf = item.get('confidence', 0.5)
                
                # 来源加权
                source = item.get('source', '')
                if source == 'rule':
                    conf = min(conf * 1.1, 0.95)  # 规则稍微提高
                elif source == 'llm':
                    conf = conf  # LLM保持原样
                elif source == 'llm_table':
                    conf = min(conf * 1.05, 0.98)  # 表格提高
                
                item['confidence'] = round(conf, 2)
        
        return results


# 置信度分级
def get_review_status(confidence: float) -> str:
    """获取复核状态"""
    if confidence >= 0.9:
        return "auto_approved"
    elif confidence >= 0.7:
        return "review_suggested"
    else:
        return "review_required"


if __name__ == "__main__":
    recognizer = UnifiedRecognizer()
    texts = [
        "K4+456 七铁塘桥 8x30m",
        "JD3 R=800 A=300 Ls=100",
        "K0+800 高程=125.45"
    ]
    result = recognizer.recognize(texts)
    print(result)
