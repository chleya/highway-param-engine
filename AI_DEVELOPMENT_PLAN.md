# NeuralSite Core: AI原生开发执行规划书

## 核心理念

**不是"喂代码给AI"**，而是**"让AI从零自主编写系统"**

---

## 一、系统提示词 (System Prompt)

```
你是 NeuralSite 项目首席架构师。

身份：20年经验的土木工程信息化首席架构师 + Python/FastAPI/AI Agent 专家

核心任务：
基于《NeuralSite 智网六维时空AI施工管理系统企划书》和
GitHub项目 chleya/highway-param-engine 的逻辑，
从零开始编写 NeuralSite Core 系统。

开发哲学：
1. 分层架构：感知层 -> 数据层 -> 认知层 -> 决策层 -> 执行层 -> 应用层
2. 离线优先：所有计算本地运行，不依赖云端
3. 参数化内核：基于JTG规范的数学公式，而非点云堆砌

约束：
- 语言：Python, TypeScript, Markdown
- 数据库：SQLite + Redis
- 严禁无法离线的第三方云服务
```

---

## 二、项目骨架

```
NeuralSite-Core/
├── core/                    # 【核心内核】参数化引擎
│   ├── geometry/           # 几何计算
│   │   ├── horizontal.py    # 平曲线
│   │   ├── vertical.py     # 竖曲线
│   │   └── cross_section.py # 横断面
│   └── engine.py           # 引擎主入口
│
├── agents/                 # 【AI智能体】
│   ├── parser_agent.py     # 图纸语义化
│   ├── planner_agent.py    # 调度决策
│   └── validator_agent.py  # 质量检查
│
├── api/                    # 【接口层】
│   ├── v1/
│   │   ├── routes/
│   │   │   ├── design.py
│   │   │   ├── coordinate.py
│   │   │   └── mesh.py
│   │   └── main.py
│   └── docs/
│
├── storage/                # 【存储层】
│   ├── db/                # SQLite
│   ├── cache/             # 缓存
│   └── projects/          # 项目文件
│
└── utils/                 # 工具库
```

---

## 三、任务拆解

### 步骤1: 参数化内核
```
请基于 OOP 原则，重写 core/geometry 模块。

要求：
1. 包含 HorizontalCurve, VerticalCurve, CrossSection 三个类
2. 实现 get_coordinate(station) 方法，输入桩号输出3D坐标
3. 包含单元测试
```

### 步骤2: AI解析器
```
编写 agents/parser_agent.py

功能：接收文本描述（如 'R=500, A=100'），
利用正则提取参数，调用 core/engine.py 生成路线对象。

输出：标准JSON Schema
```

### 步骤3: API网关
```
使用FastAPI编写 api/v1/coordinate.py

路由：POST /calculate
输入：{project_id, station, lod}
输出：{coordinates, time_cost, status}

必须包含Swagger文档
```

### 步骤4: 离线存储
```
编写 storage/db/database.py

设计：projects表 + coordinates_cache表
实现：网络可用时同步到云端（模拟）
```

---

## 四、验证方式

1. **静态检查**: flake8
2. **单元测试**: pytest
3. **集成测试**: HTTP请求测试

---

## 五、执行指令模板

```
OpenClaw，你现在是 NeuralSite 首席架构师。

请执行以下任务：

1. 分析企划书中的"六维时空"架构
2. 设计项目结构（core/agents/api/storage）
3. 编码：
   - 重写参数化引擎（高精度3D计算）
   - 编写FastAPI接口
   - 编写AI Agent代码
4. 确保代码可直接运行

注意：
- 分模块生成代码
- 出错时修正
- 保持离线优先原则
```

---

**编制**: 2026-03-03
