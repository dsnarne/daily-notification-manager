"""
Assistant API: accept a simple text prompt to trigger actions.
Supported patterns (MVP):
- tool: <name> args: { json }
- create rule { json }
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import json
import logging

from ...services.rule_service import RuleService

logger = logging.getLogger(__name__)
router = APIRouter()


class PromptRequest(BaseModel):
    prompt: str


def _try_import_mcp():
    try:
        from ...core.mcp_client import MCPCommunicationClient  # type: ignore
        return MCPCommunicationClient
    except Exception:
        return None


@router.post("/run")
async def run_prompt(req: PromptRequest) -> Dict[str, Any]:
    text = req.prompt.strip()
    # TOOL CALL: "tool: name args: {...}"
    if text.lower().startswith("tool:"):
        mcp = _try_import_mcp()
        if mcp is None:
            raise HTTPException(status_code=400, detail="MCP not available on server")
        try:
            # naive parse
            # e.g., tool: slack_list_channels args: {"limit": 10}
            after_tool = text.split(":", 1)[1].strip()
            parts = after_tool.split("args:", 1)
            name = parts[0].strip()
            args: Dict[str, Any] = {}
            if len(parts) > 1:
                json_str = parts[1].strip()
                args = json.loads(json_str)
            result = await mcp.call_tool(name, args)
            return {"action": "tool", "name": name, "args": args, "result": result}
        except Exception as e:
            logger.error(f"Tool run failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # CREATE RULE: "create rule {json}"
    if text.lower().startswith("create rule"):
        try:
            json_start = text.find("{")
            if json_start == -1:
                raise ValueError("Expected JSON body after 'create rule'")
            body = json.loads(text[json_start:])
            # Best-effort pass-through to RuleService (stubbed)
            svc = RuleService(None)
            created = await svc.create_rule(type("Obj", (), {"model_dump": lambda self=body: body})())
            return {"action": "create_rule", "input": body, "result": created}
        except Exception as e:
            logger.error(f"Create rule failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # Unknown
    return {"error": "Unsupported prompt. Use 'tool: <name> args: {...}' or 'create rule { ... }'"}


