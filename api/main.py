# -*- coding: utf-8 -*-
"""
FastAPI主应用
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
from datetime import datetime

from src import HighwayParamSystem
from src.storage import SQLiteStorage

# 创建应用
app = FastAPI(
    title="Highway Parameter Engine API",
    description="公路参数化建模系统API",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局系统
system = HighwayParamSystem(storage_type="sqlite")
storage = SQLiteStorage()


# ========== 数据模型 ==========

class CalculateRequest(BaseModel):
    route_id: str
    stake: float
    lod: Optional[str] = "LOD1"


class CalculateRangeRequest(BaseModel):
    route_id: str
    start: float
    end: float
    interval: Optional[float] = 100


class ReviewRequest(BaseModel):
    item_id: str
    decision: str  # approve/reject/modify
    value: Optional[dict] = None
    comment: Optional[str] = ""


# ========== 路由 ==========

@app.get("/")
async def root():
    return {"message": "Highway Parameter Engine API", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/v1/parse")
async def parse_file(
    file: UploadFile = File(...),
    route_id: str = Form(...),
    file_type: Optional[str] = Form(None)
):
    """上传图纸并解析"""
    
    # 保存临时文件
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 处理
        result = system.process_file(tmp_path, route_id)
        
        return {
            "status": "success",
            "route_id": route_id,
            "task_id": f"{route_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "parameters": result["parameters"],
            "validation": result["validation"],
            "review_count": len([r for r in result["review_queue"] if r["needs_review"]])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        os.unlink(tmp_path)


@app.get("/api/v1/result/{route_id}")
async def get_result(route_id: str):
    """获取解析结果"""
    
    params = storage.get_route(route_id)
    if not params:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {
        "route_id": route_id,
        "parameters": params,
        "storage": "sqlite"
    }


@app.get("/api/v1/routes")
async def list_routes():
    """列出所有路线"""
    routes = storage.list_routes()
    return {"routes": routes}


@app.post("/api/v1/calculate")
async def calculate(req: CalculateRequest):
    """计算单点坐标"""
    
    params = storage.get_route(req.route_id)
    if not params:
        raise HTTPException(status_code=404, detail="Route not found")
    
    from src.engine import HighwayEngine
    engine = HighwayEngine()
    engine.load_from_params(params)
    
    result = engine.calculate_3d(req.stake)
    result["lod"] = req.lod
    
    return result


@app.post("/api/v1/calculate/range")
async def calculate_range(req: CalculateRangeRequest):
    """批量计算坐标"""
    
    params = storage.get_route(req.route_id)
    if not params:
        raise HTTPException(status_code=404, detail="Route not found")
    
    from src.engine import HighwayEngine
    engine = HighwayEngine()
    engine.load_from_params(params)
    
    results = engine.calculate_range(req.start, req.end, req.interval)
    
    return {
        "route_id": req.route_id,
        "start": req.start,
        "end": req.end,
        "interval": req.interval,
        "count": len(results),
        "points": results
    }


@app.get("/api/v1/review/pending")
async def get_pending_reviews():
    """获取待复核列表"""
    
    reviews = storage.get_pending_reviews()
    return {"pending": reviews, "count": len(reviews)}


@app.post("/api/v1/review")
async def submit_review(req: ReviewRequest):
    """提交复核结果"""
    
    from src.review import ReviewManager
    reviewer = ReviewManager()
    
    if req.decision == "approve":
        success = reviewer.approve(req.item_id, comment=req.comment)
    elif req.decision == "reject":
        success = reviewer.reject(req.item_id, comment=req.comment)
    elif req.decision == "modify":
        success = reviewer.modify(req.item_id, req.value or {}, comment=req.comment)
    else:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    if success:
        return {"status": "success", "item_id": req.item_id, "decision": req.decision}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/api/v1/stats")
async def get_stats():
    """获取统计信息"""
    
    from src.review import ReviewManager
    reviewer = ReviewManager()
    stats = reviewer.get_stats()
    
    return {
        "routes": len(storage.list_routes()),
        "reviews": stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
