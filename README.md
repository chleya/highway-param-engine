# Highway Parameter Engine

公路参数化计算引擎

## 功能

- 平曲线坐标计算（直线/圆曲线/缓和曲线）
- 纵曲线高程计算（坡度/竖曲线）
- 三维坐标实时计算
- LOD分级采样
- JSON数据加载

## 使用

```python
from highway_param_engine import HighwayParamEngine

engine = HighwayParamEngine()
engine.load_from_json(data)

# 计算坐标
result = engine.calculate_3d(500)  # 桩号500m
print(result)  # {stake, x, y, z, azimuth}
```

## 参考

- JTG D20-2017《公路路线设计规范》
- JTG/T 2420-2021《公路工程信息模型应用统一标准》
