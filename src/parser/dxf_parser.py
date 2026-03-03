# -*- coding: utf-8 -*-
"""
DXF图纸解析器
"""

import ezdxf
from typing import Dict, List, Any
import re


class DXFParser:
    """DXF文件解析器"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.doc = None
        self.texts = []
        self.blocks = []
        self.layers = []
        self.points = []
        
    def parse(self) -> Dict:
        """解析DXF文件"""
        try:
            self.doc = ezdxf.readfile(self.filepath)
            return {
                "texts": self._extract_texts(),
                "blocks": self._extract_blocks(),
                "layers": self._extract_layers(),
                "points": self._extract_points(),
                "entities": self._extract_entities()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_texts(self) -> List[Dict]:
        """提取文字"""
        texts = []
        
        # MTEXT
        for mtext in self.doc.modelspace().query('MTEXT'):
            texts.append({
                "type": "mtext",
                "text": mtext.text,
                "layer": mtext.dxf.layer,
                "insert": getattr(mtext.dxf, 'insert', None),
                "char_height": getattr(mtext.dxf, 'char_height', 0),
                "attachment_point": getattr(mtext.dxf, 'attachment_point', None)
            })
        
        # TEXT
        for text in self.doc.modelspace().query('TEXT'):
            texts.append({
                "type": "text",
                "text": text.dxf.text,
                "layer": text.dxf.layer,
                "insert": (text.dxf.insert.x, text.dxf.insert.y),
                "height": text.dxf.height
            })
        
        self.texts = texts
        return texts
    
    def _extract_blocks(self) -> List[Dict]:
        """提取块"""
        blocks = []
        
        for block in self.doc.blocks:
            if block.name.startswith('*'):
                continue
            blocks.append({
                "name": block.name,
                "base_point": block.base_point,
                "entity_count": len(block)
            })
        
        self.blocks = blocks
        return blocks
    
    def _extract_layers(self) -> List[str]:
        """提取图层"""
        layers = [layer.dxf.name for layer in self.doc.layers]
        self.layers = layers
        return layers
    
    def _extract_points(self) -> List[Dict]:
        """提取点坐标"""
        points = []
        
        for point in self.doc.modelspace().query('POINT'):
            points.append({
                "layer": point.dxf.layer,
                "location": (point.dxf.location.x, point.dxf.location.y)
            })
        
        self.points = points
        return points
    
    def _extract_entities(self) -> Dict:
        """提取实体统计"""
        return {
            "total_entities": len(list(self.doc.modelspace())),
            "by_type": self._count_by_type()
        }
    
    def _count_by_type(self) -> Dict:
        """按类型统计"""
        counts = {}
        for entity in self.doc.modelspace():
            dxftype = entity.dxftype()
            counts[dxftype] = counts.get(dxftype, 0) + 1
        return counts
    
    def find_tables(self) -> List[Dict]:
        """查找表格（通过文字布局识别）"""
        tables = []
        
        # 简单的表格检测：查找排列规则的文字
        text_positions = []
        for t in self.texts:
            if t.get('insert'):
                text_positions.append((t['insert'][0], t['insert'][1], t['text']))
        
        # 按Y坐标分组（近似行）
        if text_positions:
            text_positions.sort(key=lambda x: -x[1])  # Y降序
            
            current_row = []
            current_y = None
            threshold = 5  # 5单位内视为同一行
            
            for x, y, text in text_positions:
                if current_y is None:
                    current_y = y
                    current_row = [(x, y, text)]
                elif abs(y - current_y) < threshold:
                    current_row.append((x, y, text))
                else:
                    if len(current_row) > 2:  # 超过2列可能是表格
                        tables.append({
                            "type": "suspect_table",
                            "rows": sorted(current_row, key=lambda r: r[0])
                        })
                    current_row = [(x, y, text)]
                    current_y = y
        
        return tables
    
    def extract_by_layer(self, layer_name: str) -> List[Dict]:
        """按图层提取"""
        result = {
            "texts": [t for t in self.texts if t.get('layer') == layer_name],
            "points": [p for p in self.points if p.get('layer') == layer_name]
        }
        return result


if __name__ == "__main__":
    # 测试
    parser = DXFParser("test.dxf")
    # parser.parse()
    print("DXFParser ready")
