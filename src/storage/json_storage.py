# -*- coding: utf-8 -*-
"""
JSON存储
"""

import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class JSONStorage:
    """JSON文件存储"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def save_params(self, route_id: str, params: Dict) -> str:
        """保存参数"""
        filepath = self.base_path / f"{route_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        
        data = {
            "route_id": route_id,
            "extracted_at": datetime.now().isoformat(),
            "parameters": params
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def load_params(self, route_id: str) -> Dict:
        """加载最新参数"""
        files = sorted(self.base_path.glob(f"{route_id}_*.json"), reverse=True)
        
        if not files:
            return None
        
        with open(files[0], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_routes(self) -> list:
        """列出所有路线"""
        routes = set()
        for f in self.base_path.glob("*.json"):
            name = f.stem
            if '_' in name:
                routes.add(name.rsplit('_', 1)[0])
        return sorted(routes)


if __name__ == "__main__":
    storage = JSONStorage()
    print(storage.list_routes())
