# -*- coding: utf-8 -*-
"""
命令行入口
"""

import argparse
import sys
import json
from pathlib import Path

from src import HighwayCalculator, create_sample_data, setup_logging


def main():
    parser = argparse.ArgumentParser(description="Highway Parameter Engine")
    
    parser.add_argument('command', choices=['calculate', 'demo', 'serve'],
                       help='命令')
    
    parser.add_argument('--stake', '-s', help='桩号')
    parser.add_argument('--start', help='起点桩号')
    parser.add_argument('--end', help='终点桩号')
    parser.add_argument('--interval', '-i', type=float, default=100, help='间隔')
    parser.add_argument('--lod', choices=['LOD0', 'LOD1', 'LOD2'], help='LOD级别')
    parser.add_argument('--input', '-f', help='输入JSON文件')
    parser.add_argument('--output', '-o', help='输出JSON文件')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    if args.command == 'calculate':
        # 加载数据
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = create_sample_data()
        
        calc = HighwayCalculator()
        calc.load_from_json(data)
        
        # 计算
        if args.stake:
            s = calc._parse_stake(args.stake)
            result = calc.calculate_3d(s)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.start and args.end:
            s1 = calc._parse_stake(args.start)
            s2 = calc._parse_stake(args.end)
            
            if args.lod:
                results = calc.calculate_lod(s1, s2, args.lod)
            else:
                results = calc.calculate_range(s1, s2, args.interval)
            
            output = {
                "start": args.start,
                "end": args.end,
                "count": len(results),
                "points": results
            }
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, ensure_ascii=False, indent=2)
                print(f"已保存到 {args.output}")
            else:
                print(json.dumps(output, ensure_ascii=False, indent=2))
    
    elif args.command == 'demo':
        print("启动Web演示...")
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "demo/app.py"])
    
    elif args.command == 'serve':
        print("启动API服务...")
        import subprocess
        subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--reload"])


if __name__ == "__main__":
    main()
