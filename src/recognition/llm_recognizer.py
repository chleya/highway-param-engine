# -*- coding: utf-8 -*-
"""
LLM识别器 - MiniMax
"""

import sys
import json
import re
from typing import Dict, List, Any

# MiniMax路径
sys.path.insert(0, 'F:/ai_partner_evolution')


class LLMRecognizer:
    """MiniMax LLM识别器"""
    
    def __init__(self):
        self.client = None
        self._init_client()
        
    def _init_client(self):
        """初始化MiniMax客户端"""
        try:
            from src.utils.llm_client import MiniMaxClient
            self.client = MiniMaxClient()
        except ImportError:
            print("Warning: MiniMax not available")
            
    def recognize(self, texts: List[str], context: str = "") -> Dict:
        """识别参数"""
        if not self.client:
            return {"error": "MiniMax not available"}
        
        # 构建prompt
        prompt = self._build_prompt(texts, context)
        
        try:
            result = self.client.generate(
                prompt,
                system_prompt=self._system_prompt(),
                temperature=0.3
            )
            
            # 解析JSON
            params = self._parse_json(result)
            
            # 添加置信度
            params = self._add_confidence(params)
            
            return params
            
        except Exception as e:
            return {"error": str(e)}
    
    def _system_prompt(self) -> str:
        """系统提示词"""
        return """你是公路设计专家。从图纸文本中提取路线设计参数。

只提取以下参数，不要猜测：
- 平曲线: JD桩号、X/Y坐标、偏角Δ、半径R、回旋参数A、缓和长Ls
- 纵曲线: 变坡点桩号、高程、前后坡度i1/i2、竖曲线长L
- 结构物: 名称、桩号、跨数x跨径、类型

输出JSON格式，每个参数附置信度(0-1)。"""
    
    def _build_prompt(self, texts: List[str], context: str) -> str:
        """构建Prompt"""
        # 取关键文字
        key_texts = []
        for t in texts:
            if len(t) > 2 and any(c.isdigit() for c in str(t)):
                key_texts.append(str(t))
        
        sample = "\n".join(key_texts[:80])
        
        prompt = f"""
从以下图纸文本提取参数。输出JSON。

{sample}

{context}

输出格式:
{{
  "horizontal_alignment": [
    {{"element_type":"","start_stake":"","R":0,"A":0,"Ls":0,"confidence":0}}
  ],
  "vertical_alignment": [
    {{"stake":"","elevation":0,"grade_in":0,"grade_out":0,"curve_length":0,"confidence":0}}
  ],
  "structures": [
    {{"type":"","name":"","stake":"","spans":"","confidence":0}}
  ]
}}
"""
        return prompt
    
    def _parse_json(self, text: str) -> Dict:
        """解析JSON"""
        # 查找JSON块
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}
    
    def _add_confidence(self, params: Dict) -> Dict:
        """添加置信度"""
        # 简化：所有参数给0.85基础置信度
        for key in ['horizontal_alignment', 'vertical_alignment', 'structures']:
            if key in params and isinstance(params[key], list):
                for item in params[key]:
                    if 'confidence' not in item:
                        item['confidence'] = 0.85
        return params
    
    def recognize_table(self, table: List[List[str]]) -> Dict:
        """识别表格"""
        if not self.client:
            return {"error": "MiniMax not available"}
        
        # 表格转文本
        table_text = "\n".join([" | ".join(row) for row in table[:20]])
        
        prompt = f"""
这是图纸中的表格。提取参数。输出JSON。

{table_text}
"""
        
        try:
            result = self.client.generate(
                prompt,
                system_prompt=self._system_prompt(),
                temperature=0.3
            )
            return self._parse_json(result)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    recognizer = LLMRecognizer()
    print("LLMRecognizer ready")
