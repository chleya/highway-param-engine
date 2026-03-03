# Highway Parameter Engine

公路参数化建模系统

## 安装

```bash
pip install -r requirements.txt
```

## 依赖

- ezdxf >= 0.18
- pdfplumber >= 0.10
- pytesseract >= 0.3
- Pillow >= 10
- neo4j >= 5
- requests >= 2.28

## 使用

```python
from src import HighwayParamSystem

# 处理图纸
system = HighwayParamSystem(storage_type="sqlite")
result = system.process_file("road.dxf", "LK-2026-001")

# 计算坐标
coord = system.calculate("LK-2026-001", 500)
print(coord)
```

## 模块

- `parser` - DXF/PDF/OCR解析
- `recognition` - LLM+规则识别
- `validation` - 置信度+反向验证
- `review` - 人工复核
- `storage` - JSON/SQLite/Neo4j存储
- `engine` - 参数计算引擎

## License

MIT
