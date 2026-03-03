# -*- coding: utf-8 -*-
"""
SQLite存储
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class SQLiteStorage:
    """SQLite本地存储"""
    
    def __init__(self, db_path: str = "highway.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 路线表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT UNIQUE,
                design_speed INTEGER,
                extracted_at TEXT,
                params_json TEXT
            )
        ''')
        
        # 复核记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT,
                param_type TEXT,
                param_key TEXT,
                param_value TEXT,
                confidence REAL,
                status TEXT,
                reviewer TEXT,
                decision TEXT,
                comment TEXT,
                created_at TEXT,
                reviewed_at TEXT
            )
        ''')
        
        # 计算历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT,
                stake REAL,
                x REAL,
                y REAL,
                z REAL,
                azimuth REAL,
                calculated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_route(self, route_id: str, params: Dict, design_speed: int = 80) -> bool:
        """保存路线参数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO routes (route_id, design_speed, extracted_at, params_json)
                VALUES (?, ?, ?, ?)
            ''', (route_id, design_speed, datetime.now().isoformat(), json.dumps(params, ensure_ascii=False)))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            conn.close()
    
    def get_route(self, route_id: str) -> Optional[Dict]:
        """获取路线"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT params_json FROM routes WHERE route_id = ?', (route_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def list_routes(self) -> List[str]:
        """列出路线"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT route_id FROM routes ORDER BY extracted_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [r[0] for r in rows]
    
    def save_review(self, review: Dict) -> bool:
        """保存复核记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO reviews (route_id, param_type, param_key, param_value, 
                                    confidence, status, reviewer, decision, comment,
                                    created_at, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review.get('route_id'),
                review.get('param_type'),
                review.get('param_key'),
                review.get('param_value'),
                review.get('confidence'),
                review.get('status'),
                review.get('reviewer'),
                review.get('decision'),
                review.get('comment'),
                review.get('created_at'),
                review.get('reviewed_at')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            conn.close()
    
    def get_pending_reviews(self, route_id: str = None) -> List[Dict]:
        """获取待复核"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if route_id:
            cursor.execute('SELECT * FROM reviews WHERE status = ? AND route_id = ?', 
                         ('pending', route_id))
        else:
            cursor.execute('SELECT * FROM reviews WHERE status = ?', ('pending',))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def save_calculation(self, route_id: str, stake: float, x: float, y: float, z: float, azimuth: float):
        """保存计算结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO calculations (route_id, stake, x, y, z, azimuth, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (route_id, stake, x, y, z, azimuth, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()


if __name__ == "__main__":
    storage = SQLiteStorage()
    print(storage.list_routes())
