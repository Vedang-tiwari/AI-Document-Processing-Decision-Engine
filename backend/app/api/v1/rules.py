from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.db.session import get_db
from backend.app.db.models.models import BusinessRule
from backend.app.core.security import require_role, CurrentUser
from backend.app.core.exceptions import AppException
from backend.app.services.business_rules import BusinessRuleEngine

router = APIRouter(prefix="/rules", tags=["Business Rules"])


class RulePatchRequest(BaseModel):
    enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


@router.get("", summary="List all business rules and configurations")
def list_rules(
    current_user: CurrentUser = Depends(require_role("admin", "reviewer", "operator")),
    db: Session = Depends(get_db),
):
    rules = db.query(BusinessRule).all()
    # If DB table hasn't been seeded from YAML yet, load from YAML
    if not rules:
        yaml_rules = BusinessRuleEngine.load_rules_from_config()
        return yaml_rules
    return [
        {
            "id": r.id,
            "rule_code": r.rule_code,
            "name": r.name,
            "description": r.description,
            "document_type": r.document_type,
            "severity": r.severity,
            "enabled": r.enabled,
            "version": r.version,
            "configuration": r.configuration,
        }
        for r in rules
    ]


@router.patch("/{rule_code}", summary="Update business rule configuration or toggle enabled state")
def patch_rule(
    rule_code: str,
    body: RulePatchRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rule = db.query(BusinessRule).filter(BusinessRule.rule_code == rule_code).first()
    if not rule:
        raise AppException(404, "RULE_NOT_FOUND", f"Rule '{rule_code}' not found.")

    if body.enabled is not None:
        rule.enabled = body.enabled
    if body.configuration is not None:
        rule.configuration = body.configuration
    rule.version += 1
    db.commit()

    return {
        "status": "success",
        "rule_code": rule.rule_code,
        "enabled": rule.enabled,
        "version": rule.version,
        "configuration": rule.configuration,
    }
