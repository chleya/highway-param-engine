# -*- coding: utf-8 -*-
"""
PDF图纸解析器
"""

import pdfplumber
from typing import Dict, List, Any
import re


class PDFParser:
    """PDF文件解析器"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.pdf = None
        self.pages = []
        
    def parse(self) -> Dict:
        """解析PDF文件"""
        try:
            with pdfplumber.open(self.filepath) as pdf:
                self.pdf = pdf
                return {
                    "page_count": len(pdf.pages),
                    "pages": self._extract_pages(),
                    "tables": self._extract_tables(),
                    "texts": self._extract_texts()
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_pages(self) -> List[Dict]:
        """提取页面信息"""
        pages = []
        
        for i, page in enumerate(self.pdf.pages):
            pages.append({
                "page_number": i + 1,
                "width": page.width,
                "height": page.height,
                "提取文字数": len(page.extract_words())
            })
        
        self.pages = pages
        return pages
    
    def _extract_texts(self) -> List[Dict]:
        """提取文字"""
        texts = []
        
        for page_num, page in enumerate(self.pdf.pages):
            # 提取文字
            page_text = page.extract_text()
            if page_text:
                # 按行分割
                lines = page_text.split('\n')
                for line in lines:
                    if line.strip():
                        texts.append({
                            "page": page_num + 1,
                            "text": line.strip(),
                            "line_raw": line
                        })
            
            # 提取单词（带位置）
            words = page.extract_words()
            for word in words:
                texts.append({
                    "page": page_num + 1,
                    "text": word.get('text', ''),
                    "x0": word.get('x0'),
                    "top": word.get('top'),
                    "x1": word.get('x1'),
                    "bottom": word.get('bottom')
                })
        
        return texts
    
    def _extract_tables(self) -> List[Dict]:
        """提取表格"""
        tables = []
        
        for page_num, page in enumerate(self.pdf.pages):
            page_tables = page.extract_tables()
            
            for table_idx, table in enumerate(page_tables):
                if table:
                    tables.append({
                        "page": page_num + 1,
                        "table_index": table_idx,
                        "rows": table,
                        "row_count": len(table),
                        "col_count": len(table[0]) if table else 0
                    })
        
        return tables
    
    def find_parameter_tables(self) -> List[Dict]:
        """查找参数表（JD表、变坡点表等）"""
        parameter_tables = []
        
        for table in self._extract_tables():
            rows = table.get('rows', [])
            if not rows:
                continue
            
            # 检查表头关键词
            header_text = ' '.join([str(cell) for cell in rows[0]]).upper()
            
            if any(kw in header_text for kw in ['JD', '交点', '桩号', '半径', 'R=']):
                table['table_type'] = 'horizontal_alignment'
                parameter_tables.append(table)
                
            elif any(kw in header_text for kw in ['变坡', '纵坡', '高程', '坡度', 'i=']):
                table['table_type'] = 'vertical_alignment'
                parameter_tables.append(table)
                
            elif any(kw in header_text for kw in ['桥', '涵', '隧道', '跨径']):
                table['table_type'] = 'structures'
                parameter_tables.append(table)
        
        return parameter_tables
    
    def extract_key_texts(self) -> List[str]:
        """提取关键文字（工程参数相关）"""
        key_texts = []
        keywords = [
            'K0+', 'K1+', 'JD', 'R=', 'A=', 'Ls=', 'i=',
            '半径', '桩号', '高程', '坡度', '跨径', '桥', '涵', '隧道'
        ]
        
        for text in self._extract_texts():
            txt = text.get('text', '')
            if any(kw in txt.upper() for kw in [k.upper() for k in keywords]):
                key_texts.append(txt)
        
        return key_texts


if __name__ == "__main__":
    parser = PDFParser("test.pdf")
    print("PDFParser ready")
