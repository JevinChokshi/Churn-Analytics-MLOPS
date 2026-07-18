from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
YAML_PATH = BASE_DIR / "config.yaml"


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _load_yaml() -> Dict[str, Any]:
    if not YAML_PATH.exists():
        return {}
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def get_config() -> Dict[str, Any]:
    yaml_cfg = _load_yaml()

    defaults = {
        "database": {
            "username": "postgres",
            "password": "",
            "host": "localhost",
            "port": 5432,
            "database": "customer_ltv_and_churn",
            "schema": "analytics",
            "source_table": "churn_predictions",
            "audit_table": "churn_action_audit",
        },
        "n8n": {
            "base_url": "http://localhost:5678",
            "dispatch_path": "/webhook/churn-ops",
            "timeout_seconds": 20,
            "auth_mode": "header",
            "api_key_header": "X-API-Key",
            "api_key_value": "",
            "basic_user": "",
            "basic_password": "",
            "verify_ssl": False,
        },
        "app": {
            "app_user": "operations_manager",
            "app_title": "Churn Command Center",
        },
    }

    cfg = _deep_merge(defaults, yaml_cfg)

    return cfg
