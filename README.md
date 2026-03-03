# Highway Parameter Engine

🛣️ 公路参数化建模系统

## 功能

- 从CAD/PDF图纸自动提取路线参数
- 参数化坐标计算（平曲线/纵曲线/横断面）
- LOD动态精度
- 人工复核
- REST API服务

## 安装

```bash
# 核心依赖
pip install -r requirements.txt

# API服务
pip install -r requirements-api.txt

# Web演示
pip install streamlit pandas
```

## 快速开始

### 1. Web演示

```bash
streamlit run demo/app.py
```

### 2. API服务

```bash
python -m uvicorn api.main:app --reload
```

### 3. Python使用

```python
from src.engine.highway_calculator import HighwayCalculator, create_sample_data

# 创建计算器
calc = HighwayCalculator()

# 加载数据
calc.load_from_json(create_sample_data())

# 计算坐标
result = calc.calculate_3d(500)
print(result)

# 批量计算
results = calc.calculate_range(0, 1000, 50)
```

## API接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/v1/parse` | POST | 解析图纸 |
| `/api/v1/calculate` | POST | 计算坐标 |
| `/api/v1/review` | POST | 提交复核 |

## 项目结构

```
highway-param-engine/
├── src/
│   ├── parser/       # CAD/PDF解析
│   ├── recognition/  # LLM+规则识别
│   ├── validation/  # 置信度验证
│   ├── review/       # 人工复核
│   ├── storage/      # 存储
│   └── engine/       # 计算引擎
├── api/              # FastAPI
├── demo/             # Streamlit演示
└── tests/            # 测试
```

## 技术规范

- JTG D20-2017《公路路线设计规范》
- JTG/T 2420-2021《公路工程信息模型应用统一标准》

## License

MIT
