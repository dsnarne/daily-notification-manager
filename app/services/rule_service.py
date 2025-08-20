"""Minimal RuleService stub to satisfy API imports.
Replace with real implementation when ready.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session


class RuleService:
    def __init__(self, db: Optional[Session]):
        self.db = db

    async def create_rule(self, rule) -> Dict[str, Any]:
        try:
            data = rule.model_dump() if hasattr(rule, "model_dump") else dict(rule)
        except Exception:
            data = {}
        return {"id": 1, **data}

    async def list_rules(self, user_id: Optional[int] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        return []

    async def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        return None

    async def update_rule(self, rule_id: int, rule) -> Optional[Dict[str, Any]]:
        try:
            data = rule.model_dump() if hasattr(rule, "model_dump") else dict(rule)
        except Exception:
            data = {}
        return {"id": rule_id, **data}

    async def delete_rule(self, rule_id: int) -> bool:
        return True

    async def activate_rule(self, rule_id: int) -> bool:
        return True

    async def deactivate_rule(self, rule_id: int) -> bool:
        return True

    async def test_rule(self, rule_id: int, test_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"rule_id": rule_id, "result": "ok", "input": test_data}

    async def bulk_apply_rules(self, notification_ids: List[int]) -> List[int]:
        return notification_ids


