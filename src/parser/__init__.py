# -*- coding: utf-8 -*-
"""
统一解析接口
"""

from typing import Dict, List, Any
from pathlib import Path


class UnifiedParser:
    """统一解析接口"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file_type = self._detect_type(filepath)
        self.parser = None
        
    def _detect_type(self, filepath: str) -> str:
        """检测文件类型"""
        ext = Path(filepath).suffix.lower()
        
        type_map = {
            '.dxf': 'dxf',
            '.dwg': 'dwg',
            '.pdf': 'pdf',
            '.png': 'png',
            '.jpg': 'jpg',
            '.jpeg': 'jpeg',
            '.tif': 'tif',
            '.tiff': 'tiff'
        }
        
        return type_map.get(ext, 'unknown')
    
    def parse(self) -> Dict:
        """解析文件"""
        if self.file_type == 'unknown':
            return {"error": f"Unsupported file type: {self.filepath}"}
        
        if self.file_type == 'dxf':
            from .dxf_parser import DXFParser
            self.parser = DXFParser(self.filepath)
            return self.parser.parse()
        
        elif self.file_type == 'pdf':
            from .pdf_parser import PDFParser
            self.parser = PDFParser(self.filepath)
            return self.parser.parse()
        
        elif self.file_type in ['png', 'jpg', 'jpeg', 'tif', 'tiff']:
            from .ocr_parser import OCRParser
            self.parser = OCRParser(self.filepath)
            return self.parser.parse()
        
        elif self.file_type == 'dwg':
            # DWG需要ezdxf或其他库
            return {"error": "DWG support: use DXF conversion"}
        
        return {"error": "Unknown error"}
    
    def extract_texts(self) -> List[str]:
        """统一提取文字"""
        if self.parser is None:
            self.parse()
        
        if self.file_type == 'dxf':
            return [t['text'] for t in self.parser.texts]
        
        elif self.file_type == 'pdf':
            return [t['text'] for t in self.parser.extract_key_texts()]
        
        elif self.file_type in ['png', 'jpg', 'jpeg', 'tif', 'tiff']:
            return self.parser.extract_lines()
        
        return []
    
    def extract_tables(self) -> List[Dict]:
        """统一提取表格"""
        if self.parser is None:
            self.parse()
        
        if self.file_type == 'dxf':
            return self.parser.find_tables()
        
        elif self.file_type == 'pdf':
            return self.parser.find_parameter_tables()
        
        elif self.file_type in ['png', 'jpg', 'jpeg', 'tif', 'tiff']:
            return self.parser.find_tables()
        
        return []


# 工厂函数
def create_parser(filepath: str) -> UnifiedParser:
    """创建解析器"""
    return UnifiedParser(filepath)


if __name__ == "__main__":
    parser = UnifiedParser("test.dxf")
    print(f"Detected type: {parser.file_type}")
