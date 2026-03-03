# -*- coding: utf-8 -*-
"""
OCR图片解析器 (扫描件)
"""

from typing import Dict, List, Any
import re


class OCRParser:
    """OCR图片解析器 (Tesseract)"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.texts = []
        self.boxes = []
        
    def parse(self) -> Dict:
        """解析图片（需要安装tesseract）"""
        try:
            import pytesseract
            from PIL import Image
            
            # 打开图片
            image = Image.open(self.filepath)
            
            # OCR识别
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 带位置的识别
            data = pytesseract.image_to_data(image, lang='chi_sim+eng', output_type=dict)
            
            texts = []
            boxes = []
            
            for i, txt in enumerate(data.get('text', [])):
                if txt.strip():
                    texts.append({
                        "text": txt,
                        "conf": data.get('conf', [0])[i],
                        "left": data.get('left', [0])[i],
                        "top": data.get('top', [0])[i],
                        "width": data.get('width', [0])[i],
                        "height": data.get('height', [0])[i]
                    })
                    boxes.append(txt)
            
            self.texts = texts
            
            return {
                "texts": texts,
                "full_text": text,
                "words": boxes
            }
            
        except ImportError:
            return {"error": "pytesseract not installed"}
        except Exception as e:
            return {"error": str(e)}
    
    def extract_lines(self) -> List[str]:
        """提取行文字"""
        if not self.texts:
            self.parse()
        
        # 按top排序分组
        lines = []
        current_line = []
        current_top = None
        threshold = 10
        
        for item in sorted(self.texts, key=lambda x: x.get('top', 0)):
            top = item.get('top', 0)
            if current_top is None:
                current_top = top
                current_line = [item['text']]
            elif abs(top - current_top) < threshold:
                current_line.append(item['text'])
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [item['text']]
                current_top = top
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def find_tables(self) -> List[Dict]:
        """通过位置检测表格"""
        if not self.texts:
            self.parse()
        
        # 简单的列检测：x坐标相近的文字
        texts_sorted = sorted(self.texts, key=lambda x: x.get('left', 0))
        
        columns = []
        current_col = []
        current_x = None
        threshold = 20
        
        for item in texts_sorted:
            x = item.get('left', 0)
            if current_x is None:
                current_x = x
                current_col = [item]
            elif abs(x - current_x) < threshold:
                current_col.append(item)
            else:
                if len(current_col) > 2:
                    columns.append(current_col)
                current_col = [item]
                current_x = x
        
        return [{"columns": columns}]


if __name__ == "__main__":
    parser = OCRParser("test.png")
    print("OCRParser ready (requires tesseract)")
