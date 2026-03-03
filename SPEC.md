# Highway Parameter Engine 技术规格书 V2.0

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        输入层                                    │
│   DXF (ezdxf)  │  PDF (pdfplumber)  │  DWG (ezdxf)  │  图片   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     解析层 (Parser)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  TextParser │  │ TableParser │  │  OCRParser  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   识别层 (Recognition)                           │
│  ┌─────────────────────┐  ┌─────────────────────┐            │
│  │  MiniMax LLM        │  │  RuleEngine         │            │
│  │  (语义理解)          │  │  (正则快速通道)      │            │
│  └─────────────────────┘  └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   验证层 (Validation)                            │
│     - 置信度评分                                                 │
│     - 反向验证 (参数计算 vs 原图坐标)                           │
│     - 一致性检查                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   复核层 (Review)                                │
│     - 高置信 (>0.9) → 自动通过                                  │
│     - 中置信 (0.7-0.9) → 提示复核                              │
│     - 低置信 (<0.7) → 强制人工确认                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   输出层 (Output)                                │
│     - JSON标准格式                                              │
│     - Neo4j图数据库                                            │
│     - SQLite本地                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   计算层 (Engine)                                │
│     - 平曲线计算                                                │
│     - 纵曲线计算                                                │
│     - 横断扫掠                                                 │
│     - LOD动态采样                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 二、数据模型

### 2.1 输入参数

```json
{
  "source_file": "road.dxf",
  "file_type": "dxf",
  "route_id": "LK-2026-001",
  "design_speed": 80,
  "extracted_at": "2026-03-03T19:00:00Z"
}
```

### 2.2 提取结果

```json
{
  "horizontal_alignment": [
    {
      "element_type": "圆曲线",
      "start_stake": "K0+550",
      "end_stake": "K1+200",
      "R": 800,
      "confidence": 0.95,
      "source_text": "JD3 R=800 Ls=100",
      "validation_status": "passed"
    }
  ],
  "vertical_alignment": [...],
  "cross_section": {...},
  "structures": [...]
}
```

### 2.3 复核记录

```json
{
  "id": "param_001",
  "parameter": "R",
  "extracted_value": 800,
  "confidence": 0.75,
  "source_text": "R=800m",
  "status": "pending_review",
  "reviewer": null,
  "decision": null,
  "comment": null,
  "reviewed_at": null
}
```

## 三、核心模块

### 3.1 Parser 模块

| 类 | 功能 | 依赖 |
|----|------|------|
| DXFParser | 解析DXF文件 | ezdxf |
| PDFParser | 解析PDF文件 | pdfplumber |
| OCRParser | 图片OCR识别 | pytesseract |
| TextExtractor | 统一文字提取接口 | - |

### 3.2 Recognition 模块

| 类 | 功能 | 依赖 |
|----|------|------|
| LLMRecognizer | MiniMax语义识别 | MiniMaxClient |
| RuleRecognizer | 正则规则快速匹配 | re |

### 3.3 Validation 模块

| 类 | 功能 |
|----|------|
| ConfidenceScorer | 置信度评分 |
| ReverseValidator | 反向验证 |
| ConsistencyChecker | 一致性检查 |

### 3.4 Review 模块

| 类 | 功能 |
|----|------|
| ReviewManager | 复核队列管理 |
| ReviewAPI | 复核接口 |

### 3.5 Storage 模块

| 类 | 功能 |
|----|------|
| JSONStorage | JSON文件存储 |
| SQLiteStorage | SQLite本地存储 |
| Neo4jStorage | Neo4j图数据库 |

### 3.6 Engine 模块

| 类 | 功能 |
|----|------|
| HighwayEngine | 公路参数计算引擎 |
| LODManager | LOD动态管理 |

## 四、置信度规则

### 4.1 评分因素

| 因素 | 权重 | 说明 |
|------|------|------|
| 来源清晰度 | 30% | 参数来自表格还是散注 |
| 数值合理性 | 30% | 是否在规范范围内 |
| 上下文一致性 | 20% | 与相邻参数是否矛盾 |
| 识别模型置信度 | 20% | LLM原始置信度 |

### 4.2 自动通过规则

- 置信度 > 0.9
- 参数在规范默认值范围内
- 与规则库精确匹配

### 4.3 强制人工规则

- 置信度 < 0.7
- 参数值超出规范范围
- 与相邻参数矛盾

## 五、反向验证

### 5.1 坐标验证

```
1. 用提取的参数计算坐标 P_calc
2. 从原图提取特征点坐标 P_orig
3. 计算误差 distance(P_calc, P_orig)
4. 若误差 < 0.5m → 验证通过
```

### 5.2 几何验证

- 曲线连续性检查
- 纵坡平滑性检查
- 横断面一致性检查

## 六、API 接口

### 6.1 上传图纸

```
POST /api/v1/parse
Content-Type: multipart/form-data

file: binary
file_type: dxf|pdf|dwg|image
route_id: string

Response: {task_id, status}
```

### 6.2 获取提取结果

```
GET /api/v1/result/{task_id}

Response: {
  status: processing|completed|failed,
  parameters: {...},
  confidence: {...},
  review_items: [...]
}
```

### 6.3 提交复核

```
POST /api/v1/review
Content-Type: application/json

{
  "item_id": "param_001",
  "decision": "approve|reject|modify",
  "value": 800,
  "comment": "确认半径800m"
}
```

### 6.4 计算坐标

```
POST /api/v1/calculate
Content-Type: application/json

{
  "stake": 500,
  "lod": "LOD1"
}

Response: {x, y, z, azimuth}
```

---

**编制**: 2026-03-03
**版本**: V2.0
