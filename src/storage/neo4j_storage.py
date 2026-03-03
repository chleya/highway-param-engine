# -*- coding: utf-8 -*-
"""
Neo4j图数据库存储
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class Neo4jStorage:
    """Neo4j图数据库存储"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self):
        """连接Neo4j"""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except ImportError:
            print("Warning: neo4j driver not installed")
        except Exception as e:
            print(f"Warning: Neo4j connection failed: {e}")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def save_route(self, route_id: str, params: Dict) -> bool:
        """保存路线"""
        if not self.driver:
            return False
        
        with self.driver.session() as session:
            # 创建路线节点
            session.run('''
                MERGE (r:Route {route_id: $route_id})
                SET r.design_speed = $design_speed,
                    r.extracted_at = $extracted_at
            ''', route_id=route_id, 
               design_speed=params.get('design_speed', 80),
               extracted_at=datetime.now().isoformat())
            
            # 保存平曲线
            for i, h in enumerate(params.get('horizontal_alignment', [])):
                session.run('''
                    MATCH (r:Route {route_id: $route_id})
                    MERGE (h:HorizontalElement {id: $id})
                    SET h.element_type = $element_type,
                        h.start_stake = $start_stake,
                        h.end_stake = $end_stake,
                        h.R = $R,
                        h.A = $A,
                        h.Ls = $Ls,
                        h.confidence = $confidence
                    MERGE (r)-[:HAS_ELEMENT]->(h)
                ''', id=f"{route_id}_h_{i}",
                   element_type=h.get('element_type', '直线'),
                   start_stake=h.get('start_stake', ''),
                   end_stake=h.get('end_stake', ''),
                   R=h.get('R', 0),
                   A=h.get('A', 0),
                   Ls=h.get('Ls', 0),
                   confidence=h.get('confidence', 0))
            
            # 保存纵曲线
            for i, v in enumerate(params.get('vertical_alignment', [])):
                session.run('''
                    MATCH (r:Route {route_id: $route_id})
                    MERGE (v:VerticalElement {id: $id})
                    SET v.stake = $stake,
                        v.elevation = $elevation,
                        v.grade_in = $grade_in,
                        v.grade_out = $grade_out,
                        v.curve_length = $curve_length,
                        v.confidence = $confidence
                    MERGE (r)-[:HAS_ELEMENT]->(v)
                ''', id=f"{route_id}_v_{i}",
                   stake=v.get('stake', ''),
                   elevation=v.get('elevation', 0),
                   grade_in=v.get('grade_in', 0),
                   grade_out=v.get('grade_out', 0),
                   curve_length=v.get('curve_length', 0),
                   confidence=v.get('confidence', 0))
            
            # 保存结构物
            for i, s in enumerate(params.get('structures', [])):
                session.run('''
                    MATCH (r:Route {route_id: $route_id})
                    MERGE (s:Structure {id: $id})
                    SET s.type = $type,
                        s.name = $name,
                        s.stake = $stake,
                        s.spans = $spans,
                        s.confidence = $confidence
                    MERGE (r)-[:HAS_STRUCTURE]->(s)
                ''', id=f"{route_id}_s_{i}",
                   type=s.get('type', ''),
                   name=s.get('name', ''),
                   stake=s.get('stake', ''),
                   spans=s.get('spans', ''),
                   confidence=s.get('confidence', 0))
        
        return True
    
    def get_route(self, route_id: str) -> Optional[Dict]:
        """获取路线"""
        if not self.driver:
            return None
        
        with self.driver.session() as session:
            result = session.run('''
                MATCH (r:Route {route_id: $route_id})
                OPTIONAL MATCH (r)-[:HAS_ELEMENT]->(h:HorizontalElement)
                OPTIONAL MATCH (r)-[:HAS_ELEMENT]->(v:VerticalElement)
                OPTIONAL MATCH (r)-[:HAS_STRUCTURE]->(s:Structure)
                RETURN r, collect(h) as horizontal, collect(v) as vertical, collect(s) as structures
            ''', route_id=route_id)
            
            record = result.single()
            if not record:
                return None
            
            r = record['r']
            return {
                "route_id": r['route_id'],
                "design_speed": r.get('design_speed'),
                "horizontal_alignment": [dict(n) for n in record['horizontal'] if n],
                "vertical_alignment": [dict(n) for n in record['vertical'] if n],
                "structures": [dict(n) for n in record['structures'] if n]
            }
    
    def find_nearby_structures(self, route_id: str, stake: float, radius: float = 100) -> List[Dict]:
        """查找附近结构物"""
        if not self.driver:
            return []
        
        with self.driver.session() as session:
            result = session.run('''
                MATCH (r:Route {route_id: $route_id})-[:HAS_STRUCTURE]->(s:Structure)
                WHERE abs(tofloat(s.stake) - $stake) < $radius
                RETURN s
            ''', route_id=route_id, stake=stake, radius=radius)
            
            return [dict(record['s']) for record in result]


if __name__ == "__main__":
    # 测试（需要Neo4j）
    storage = Neo4jStorage()
    print("Neo4j storage ready (requires Neo4j running)")
