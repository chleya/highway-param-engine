# -*- coding: utf-8 -*-
"""
配置加载器
"""

import os
import yaml
from typing import Any, Dict
from pathlib import Path


class Config:
    """配置类"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        """加载配置"""
        config_path = Path(__file__).parent / "config.yaml"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        
        # 环境变量覆盖
        self._apply_env()
    
    def _apply_env(self):
        """环境变量覆盖"""
        env_mappings = {
            'STORAGE_TYPE': ('storage', 'type'),
            'NEO4J_URI': ('neo4j', 'uri'),
            'NEO4J_USER': ('neo4j', 'user'),
            'NEO4J_PASSWORD': ('neo4j', 'password'),
            'MINIMAX_API_KEY': ('minimax', 'api_key'),
            'DEBUG': ('app', 'debug'),
        }
        
        for env_key, (section, key) in env_mappings.items():
            value = os.environ.get(env_key)
            if value:
                if section not in self._config:
                    self._config[section] = {}
                self._config[section][key] = value
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """获取配置"""
        if key is None:
            return self._config.get(section, {})
        
        return self._config.get(section, {}).get(key, default)
    
    def __getitem__(self, key: str) -> Dict:
        return self._config.get(key, {})
    
    def __repr__(self):
        return f"Config({list(self._config.keys())})"


# 全局配置
config = Config()


def get_config() -> Config:
    """获取配置实例"""
    return Config()
