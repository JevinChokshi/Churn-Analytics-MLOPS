from __future__ import annotations

import requests
from typing import Dict


class AutomationClient:
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.n8n = cfg["n8n"]

    def webhook_url(self) -> str:
        return f"{self.n8n['webhook_url']}"

    def headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-App-Source": "streamlit-churn-command-center",
        }
        if self.n8n["auth_mode"] == "header" and self.n8n.get("api_key_value"):
            headers[self.n8n["api_key_header"]] = self.n8n["api_key_value"]
        return headers

    def auth(self):
        if self.n8n["auth_mode"] == "basic":
            return (self.n8n.get("basic_user", ""), self.n8n.get("basic_password", ""))
        return None

    def dispatch(self, payload: Dict) -> Dict:
        response = requests.post(
            self.webhook_url(),
            headers=self.headers(),
            auth=self.auth(),
            json=payload,
            timeout=int(self.n8n["timeout_seconds"]),
            verify=bool(self.n8n["verify_ssl"]),
        )
        response.raise_for_status()
        try:
            body = response.json()
        except Exception:
            body = {"raw_text": response.text}
        return {
            "status_code": response.status_code,
            "url": self.webhook_url(),
            "response": body,
        }
