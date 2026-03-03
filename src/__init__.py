# -*- coding: utf-8 -*-
"""
Highway Parameter Engine
公路参数化建模系统
"""

from .config import Config, config, get_config
from .logging_config import logger, setup_logging

from .parser import UnifiedParser, create_parser
from .recognition import UnifiedRecognizer, get_review_status
from .validation import ConfidenceScorer, ReverseValidator
from .review import ReviewManager, create_review_queue
from .storage import JSONStorage, SQLiteStorage, Neo4jStorage
from .engine import HighwayCalculator, HighwayEngine, LODManager, create_sample_data


__version__ = "2.0.0"
__author__ = "Highway Team"


__all__ = [
    # 配置
    'Config', 'config', 'get_config',
    'logger', 'setup_logging',
    
    # Parser
    'UnifiedParser', 'create_parser',
    
    # Recognition
    'UnifiedRecognizer', 'get_review_status',
    
    # Validation
    'ConfidenceScorer', 'ReverseValidator',
    
    # Review
    'ReviewManager', 'create_review_queue',
    
    # Storage
    'JSONStorage', 'SQLiteStorage', 'Neo4jStorage',
    
    # Engine
    'HighwayCalculator', 'HighwayEngine', 'LODManager', 'create_sample_data',
]
