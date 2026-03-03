# -*- coding: utf-8 -*-
"""
人工复核模块
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path


class ReviewManager:
    """复核管理器"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "reviews.json"
        self.reviews = self._load()
        
    def _load(self) -> List[Dict]:
        """加载复核记录"""
        if Path(self.storage_path).exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save(self):
        """保存复核记录"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.reviews, f, ensure_ascii=False, indent=2)
    
    def create_review_items(self, params: Dict) -> List[Dict]:
        """创建复核项目"""
        items = []
        
        for key in ["horizontal_alignment", "vertical_alignment", "structures"]:
            for i, item in enumerate(params.get(key, [])):
                confidence = item.get('confidence', 0.5)
                
                # 需要复核的项目
                if confidence < 0.9:
                    review_item = {
                        "id": f"{key}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "param_type": key,
                        "index": i,
                        "parameter": item,
                        "confidence": confidence,
                        "status": "pending",
                        "reviewer": None,
                        "decision": None,
                        "comment": None,
                        "created_at": datetime.now().isoformat()
                    }
                    items.append(review_item)
                    self.reviews.append(review_item)
        
        self._save()
        return items
    
    def get_pending(self) -> List[Dict]:
        """获取待复核项目"""
        return [r for r in self.reviews if r.get('status') == 'pending']
    
    def get_auto_approved(self) -> List[Dict]:
        """获取自动通过项目"""
        return [r for r in self.reviews if r.get('status') == 'auto_approved']
    
    def approve(self, item_id: str, reviewer: str = "human", comment: str = "") -> bool:
        """批准项目"""
        return self._update_decision(item_id, "approve", reviewer, comment)
    
    def reject(self, item_id: str, reviewer: str = "human", comment: str = "") -> bool:
        """拒绝项目"""
        return self._update_decision(item_id, "reject", reviewer, comment)
    
    def modify(self, item_id: str, new_value: Dict, reviewer: str = "human", comment: str = "") -> bool:
        """修改项目"""
        for r in self.reviews:
            if r.get('id') == item_id:
                r['parameter'].update(new_value)
                r['status'] = 'modified'
                r['reviewer'] = reviewer
                r['decision'] = 'modify'
                r['comment'] = comment
                r['reviewed_at'] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def _update_decision(self, item_id: str, decision: str, reviewer: str, comment: str) -> bool:
        """更新决定"""
        for r in self.reviews:
            if r.get('id') == item_id:
                r['status'] = decision
                r['reviewer'] = reviewer
                r['decision'] = decision
                r['comment'] = comment
                r['reviewed_at'] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = len(self.reviews)
        pending = len([r for r in self.reviews if r.get('status') == 'pending'])
        approved = len([r for r in self.reviews if r.get('status') == 'approve'])
        rejected = len([r for r in self.reviews if r.get('status') == 'reject'])
        modified = len([r for r in self.reviews if r.get('status') == 'modified'])
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "modified": modified
        }


# 快速函数
def create_review_queue(params: Dict) -> List[Dict]:
    """创建复核队列"""
    from ..validation import get_review_status
    
    queue = []
    
    for key in ["horizontal_alignment", "vertical_alignment", "structures"]:
        for i, item in enumerate(params.get(key, [])):
            confidence = item.get('confidence', 0)
            status = get_review_status(confidence)
            
            queue.append({
                "id": f"{key}_{i}",
                "type": key,
                "item": item,
                "confidence": confidence,
                "status": status,
                "needs_review": status != "auto_approved"
            })
    
    return queue


if __name__ == "__main__":
    manager = ReviewManager()
    print(manager.get_stats())
