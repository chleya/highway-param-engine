# -*- coding: utf-8 -*-
"""
完整流程 - 从文件到计算
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, '.')

from src.parser import create_parser
from src.recognition import UnifiedRecognizer, get_review_status
from src.validation import ConfidenceScorer
from src.storage import SQLiteStorage
from src.engine import HighwayCalculator


class HighwayPipeline:
    """完整流程管道"""
    
    def __init__(self, storage_type: str = "sqlite"):
        self.storage = SQLiteStorage() if storage_type == "sqlite" else None
        self.recognizer = UnifiedRecognizer()
        self.scorer = ConfidenceScorer()
    
    def process_file(self, filepath: str, route_id: str = None) -> dict:
        """处理文件并提取参数"""
        route_id = route_id or Path(filepath).stem
        
        print(f"[Parse] {filepath}")
        
        # 1. 解析文件
        parser = create_parser(filepath)
        parse_result = parser.parse()
        
        if "error" in parse_result:
            return {"status": "error", "message": parse_result["error"]}
        
        # 2. 提取文字
        texts = parser.extract_texts()
        print(f"[Texts] {len(texts)} extracted")
        
        # 3. 提取表格
        tables = parser.extract_tables()
        print(f"[Tables] {len(tables)} extracted")
        
        # 4. 识别参数
        print("[Recognize] Extracting parameters...")
        params = self.recognizer.recognize(texts, tables)
        
        # 5. 置信度评分
        params = self.scorer.score_params(params)
        
        # 6. 创建复核队列
        review_queue = []
        for key in ["horizontal_alignment", "vertical_alignment", "structures"]:
            for i, item in enumerate(params.get(key, [])):
                status = get_review_status(item.get('confidence', 0))
                review_queue.append({
                    "id": f"{key}_{i}",
                    "type": key,
                    "item": item,
                    "status": status,
                    "needs_review": status != "auto_approved"
                })
        
        # 7. 保存
        if self.storage:
            self.storage.save_route(route_id, params)
            print(f"[Saved] Database updated")
        
        return {
            "status": "success",
            "route_id": route_id,
            "text_count": len(texts),
            "table_count": len(tables),
            "parameters": params,
            "review_queue": review_queue,
            "auto_approved": len([r for r in review_queue if not r['needs_review']]),
            "needs_review": len([r for r in review_queue if r['needs_review']])
        }
    
    def load_and_calculate(self, route_id: str, stake: float):
        """加载参数并计算"""
        if self.storage:
            params = self.storage.get_route(route_id)
        else:
            params = None
        
        if not params:
            return {"error": f"Route {route_id} not found"}
        
        calc = HighwayCalculator()
        calc.load_from_json(params)
        
        return calc.calculate_3d(stake)
    
    def parse_stake(self, stake_str: str) -> float:
        """解析桩号"""
        import re
        m = re.search(r'K?(\d+)\+(\d{3})', stake_str.upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Highway Pipeline")
    parser.add_argument('file', nargs='?', help='Input file')
    parser.add_argument('--route-id', '-r', help='Route ID')
    parser.add_argument('--calculate', '-c', help='Calculate stake')
    
    args = parser.parse_args()
    
    pipeline = HighwayPipeline()
    
    if not args.file:
        print("Usage:")
        print("  python pipeline.py file.dxf")
        print("  python pipeline.py file.dxf --route-id ROUTE001")
        print("  python pipeline.py file.dxf -r ROUTE001 -c K0+500")
        return
    
    result = pipeline.process_file(args.file, args.route_id)
    
    print("\n" + "="*50)
    print("[Result]")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if args.calculate and result['status'] == 'success':
        s = pipeline.parse_stake(args.calculate)
        calc_result = pipeline.load_and_calculate(result['route_id'], s)
        print("\n[Calculation]")
        print(json.dumps(calc_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
