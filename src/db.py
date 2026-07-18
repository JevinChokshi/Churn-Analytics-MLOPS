from __future__ import annotations

import json
from typing import Dict, List

import pandas as pd
import sqlalchemy
from sqlalchemy import text
from urllib.parse import quote_plus


class DatabaseClient:
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.db = cfg["database"]
        password = quote_plus(str(self.db["password"]))
        conn = (
            f"postgresql+psycopg2://{self.db['username']}:{password}"
            f"@{self.db['host']}:{self.db['port']}/{self.db['database']}"
        )
        self.engine = sqlalchemy.create_engine(conn, pool_pre_ping=True)

    def ensure_source_audit_columns(self):
        sql = f"""
        ALTER TABLE {self.db['schema']}.{self.db['source_table']}
        ADD COLUMN IF NOT EXISTS audit_action_status TEXT,
        ADD COLUMN IF NOT EXISTS audit_notes TEXT,
        ADD COLUMN IF NOT EXISTS audit_override_by TEXT,
        ADD COLUMN IF NOT EXISTS audit_override_at TIMESTAMP;
        """
        with self.engine.begin() as conn:
            conn.execute(text(sql))

    def ensure_audit_table(self):
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {self.db['schema']}.{self.db['audit_table']} (
            audit_id UUID PRIMARY KEY,
            user_account_id TEXT NOT NULL,
            allocated_operational_tier TEXT,
            action_status TEXT,
            action_taken TEXT NOT NULL,
            action_notes TEXT,
            triggered_by TEXT,
            request_id TEXT,
            automation_target TEXT,
            automation_response JSONB,
            status TEXT NOT NULL,
            event_timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.engine.begin() as conn:
            conn.execute(text(ddl))

    def load_predictions(self) -> pd.DataFrame:
        q = f"SELECT * FROM {self.db['schema']}.{self.db['source_table']};"
        return pd.read_sql(q, self.engine)

    def save_overrides(self, df_updates: pd.DataFrame) -> int:
        if df_updates.empty:
            return 0

        self.ensure_source_audit_columns()

        with self.engine.begin() as conn:
            for _, row in df_updates.iterrows():
                sql = text(f"""
                    UPDATE {self.db['schema']}.{self.db['source_table']}
                    SET
                        audit_action_status = :audit_action_status,
                        audit_notes = :audit_notes,
                        audit_override_by = :audit_override_by,
                        audit_override_at = :audit_override_at
                    WHERE user_account_id = :user_account_id
                """)
                conn.execute(
                    sql,
                    {
                        "user_account_id": row.get("user_account_id"),
                        "audit_action_status": row.get("audit_action_status"),
                        "audit_notes": row.get("audit_notes"),
                        "audit_override_by": row.get("audit_override_by"),
                        "audit_override_at": row.get("audit_override_at"),
                    },
                )
        return len(df_updates)

    def insert_audit_logs(self, logs: List[Dict]):
        if not logs:
            return
        self.ensure_audit_table()
        sql = text(f"""
            INSERT INTO {self.db['schema']}.{self.db['audit_table']} (
                audit_id,
                user_account_id,
                allocated_operational_tier,
                action_status,
                action_taken,
                action_notes,
                triggered_by,
                request_id,
                automation_target,
                automation_response,
                status,
                event_timestamp
            ) VALUES (
                :audit_id,
                :user_account_id,
                :allocated_operational_tier,
                :action_status,
                :action_taken,
                :action_notes,
                :triggered_by,
                :request_id,
                :automation_target,
                CAST(:automation_response AS JSONB),
                :status,
                :event_timestamp
            )
        """)
        with self.engine.begin() as conn:
            for row in logs:
                payload = dict(row)
                payload["automation_response"] = json.dumps(payload.get("automation_response", {}))
                conn.execute(sql, payload)

    def recent_logs(self, limit: int = 200) -> pd.DataFrame:
        self.ensure_audit_table()
        q = f"""
        SELECT *
        FROM {self.db['schema']}.{self.db['audit_table']}
        ORDER BY event_timestamp DESC
        LIMIT {int(limit)};
        """
        return pd.read_sql(q, self.engine)
