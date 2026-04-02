"""Audit logging service."""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import AuditLog


async def log_action(
    db: AsyncSession,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    outcome: str = "success",
    ip_address: Optional[str] = None,
):
    log = AuditLog(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details or {}),
        outcome=outcome,
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
    return log
