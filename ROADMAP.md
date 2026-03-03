# Highway Parameter Engine 开发计划 V2.0

## 阶段一：核心解析 (1周) ✅

- [x] DXF解析器 (ezdxf)
- [x] PDF解析器 (pdfplumber)
- [x] OCR解析器 (pytesseract)
- [x] 统一提取接口

## 阶段二：智能识别 (1周) ✅

- [x] MiniMax LLM识别
- [x] 规则引擎快速匹配
- [x] 置信度评分

## 阶段三：验证与复核 (1周) ✅

- [x] 反向坐标验证
- [x] 一致性检查
- [x] 人工复核界面/接口
- [ ] 反馈优化Prompt

## 阶段四：存储输出 (进行中)

- [ ] JSON文件存储
- [ ] SQLite本地存储
- [ ] Neo4j图数据库

## 阶段五：计算引擎 (进行中)

- [ ] 平曲线计算
- [ ] 纵曲线计算
- [ ] 横断扫掠
- [ ] LOD动态采样

## 阶段六：API服务

- [ ] FastAPI接口
- [ ] 任务队列
- [ ] Docker部署

---

## 当前进度

- Parser: DXF/PDF/OCR ✅
- Recognition: LLM + 规则 ✅
- Validation: 置信度 + 反向验证 ✅
- Review: 人工复核队列 ✅
- Storage: 进行中
- Engine: 进行中
