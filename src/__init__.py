# -*- coding: utf-8 -*-
"""
Highway Parameter Engine - 主入口
"""

from .parser import UnifiedParser, create_parser
from .recognition import UnifiedRecognizer
from .validation import ConfidenceScorer, ReverseValidator, get_review_status
from .review import ReviewManager, create_review_queue
from .storage import JSONStorage, SQLiteStorage, Neo4jStorage
from .engine import HighwayEngine, LODManager


__version__ = "2.0.0"


class HighwayParamSystem:
    """公路参数系统 - 统一入口"""
    
    def __init__(self, storage_type: str = "json"):
        self.parser = None
        self.recognizer = UnifiedRecognizer()
        self.scorer = ConfidenceScorer()
        self.validator = ReverseValidator()
        self.reviewer = ReviewManager()
        
        # 存储
        if storage_type == "json":
            self.storage = JSONStorage()
        elif storage_type == "sqlite":
            self.storage = SQLiteStorage()
        elif storage_type == "neo4j":
            self.storage = Neo4jStorage()
        else:
            self.storage = JSONStorage()
        
        self.engine = HighwayEngine()
    
    def process_file(self, filepath: str, route_id: str = None) -> Dict:
        """处理文件"""
        # 1. 解析
        self.parser = create_parser(filepath)
        parse_result = self.parser.parse()
        
        # 2. 提取文字
        texts = self.parser.extract_texts()
        
        # 3. 识别参数
        params = self.recognizer.recognize(texts)
        
        # 4. 置信度评分
        params = self.scorer.score_params(params)
        
        # 5. 验证
        validation = self.validator.validate(params)
        
        # 6. 创建复核队列
        review_queue = create_review_queue(params)
        
        # 7. 保存
        route_id = route_id or "unknown"
        self.storage.save_params(route_id, params)
        
        return {
            "route_id": route_id,
            "parse_result": parse_result,
            "parameters": params,
            "validation": validation,
            "review_queue": review_queue
        }
    
    def calculate(self, route_id: str, stake: float) -> Dict:
        """计算坐标"""
        params = self.storage.get_params(route_id)
        if not params:
            return {"error": "Route not found"}
        
        self.engine.load_from_params(params)
        return self.engine.calculate_3d(stake)
    
    def calculate_range(self, route_id: str, start: float, end: float, interval: float = 100) -> List[Dict]:
        """批量计算"""
        params = self.storage.get_params(route_id)
        if not params:
            return []
        
        self.engine.load_from_params(params)
        return self.engine.calculate_range(start, end, interval)


# 导出
__all__ = [
    'HighwayParamSystem',
    'UnifiedParser', 'create_parser',
    'UnifiedRecognizer',
    'ConfidenceScorer', 'ReverseValidator', 'get_review_status',
    'ReviewManager', 'create_review_queue',
    'JSONStorage', 'SQLiteStorage', 'Neo4jStorage',
    'HighwayEngine', 'LODManager'
]
