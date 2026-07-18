from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.automation import AutomationClient
from src.config import get_config
from src.db import DatabaseClient

AUDIT_OPTIONS = [
    "PENDING_REVIEW",
    "APPROVED",
    "BLOCKED",
    "MANUALLY_OVERRIDDEN",
    "ESCALATED_TO_CS",
    "ESCALATED_TO_SALES",
    "EMAIL_AUTOMATION_QUEUED",
    "DO_NOT_CONTACT",
]


def _inject_css():
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(55,182,255,0.14), transparent 28%),
                    radial-gradient(circle at top right, rgba(124,58,237,0.15), transparent 24%),
                    linear-gradient(180deg, #0b1020 0%, #0f172a 100%);
                color: #e5eefc;
            }
            .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 96rem;}
            [data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(2,6,23,0.98));}
            .hero {padding: 1.4rem 1.5rem; border: 1px solid rgba(148,163,184,0.18); background: linear-gradient(135deg, rgba(15,23,42,0.92), rgba(30,41,59,0.78)); border-radius: 24px; margin-bottom: 1rem;}
            .hero h1 {font-size: 2rem; line-height: 1.1; margin: 0; color: white;}
            .hero p {margin-top: 0.55rem; color: #9fb0d3; font-size: 1rem;}
            .glass {background: rgba(17,24,39,0.78); border: 1px solid rgba(148,163,184,0.18); border-radius: 18px; padding: 1rem 1rem 0.5rem 1rem; backdrop-filter: blur(16px);}
            .metric-card {background: linear-gradient(180deg, rgba(17,24,39,0.9), rgba(30,41,59,0.72)); border: 1px solid rgba(148,163,184,0.18); border-radius: 18px; padding: 1rem;}
            .metric-label {color: #9fb0d3; font-size: 0.82rem; margin-bottom: 0.15rem; text-transform: uppercase; letter-spacing: 0.08em;}
            .metric-value {color: white; font-size: 1.7rem; font-weight: 700;}
            .section-title {font-size: 1.1rem; font-weight: 700; color: white; margin-bottom: 0.25rem;}
            .section-subtitle {color: #9fb0d3; font-size: 0.92rem; margin-bottom: 0.8rem;}
            div[data-testid="stDataEditor"] {border: 1px solid rgba(148,163,184,0.18); border-radius: 16px; overflow: hidden;}
            .stButton > button {width: 100%; border-radius: 14px; min-height: 2.8rem; border: 1px solid rgba(255,255,255,0.08); background: linear-gradient(135deg, rgba(55,182,255,0.18), rgba(124,58,237,0.24)); color: white; font-weight: 600;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _only_approved(df: pd.DataFrame) -> pd.DataFrame:
    if "audit_action_status" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df["audit_action_status"].astype(str).str.upper() == "APPROVED"].copy()

def _json_safe_records(df: pd.DataFrame) -> list[dict]:
    safe_df = df.copy()

    datetime_cols = safe_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
    for col in datetime_cols:
        safe_df[col] = safe_df[col].apply(
            lambda x: x.isoformat() if pd.notnull(x) else None
        )

    safe_df = safe_df.where(pd.notnull(safe_df), None)
    return safe_df.to_dict(orient="records")

def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "audit_action_status" not in df.columns:
        df["audit_action_status"] = "PENDING_REVIEW"
    if "audit_notes" not in df.columns:
        df["audit_notes"] = ""
    if "audit_override_by" not in df.columns:
        df["audit_override_by"] = ""
    if "audit_override_at" not in df.columns:
        df["audit_override_at"] = pd.NaT
    df["audit_action_status"] = df["audit_action_status"].fillna("PENDING_REVIEW")
    return df


def _apply_filters(df: pd.DataFrame):
    out = df.copy()

    with st.sidebar:
        st.markdown("### Filters")

        search_term = st.text_input(
            "Search any field",
            placeholder="USR-102 / email / name",
        )

        status_filter = st.multiselect(
            "Audit status",
            options=sorted(out["audit_action_status"].dropna().astype(str).unique().tolist()),
            default=[],
        )

        # -----------------------------
        # CATEGORICAL FILTERS
        # -----------------------------
        categorical_cols = [
            "region",
            "currency",
            "registration_plan_code",
            "industry_type",
        ]

        categorical_filter_values = {}

        with st.expander("Categorical filters", expanded=True):
            for col in categorical_cols:
                if col in out.columns:
                    options = sorted(
                        [x for x in out[col].dropna().astype(str).unique().tolist() if x != ""]
                    )
                    selected = st.multiselect(
                        f"{col}",
                        options=options,
                        default=[],
                        key=f"cat_filter_{col}",
                    )
                    categorical_filter_values[col] = selected

        # -----------------------------
        # NUMERIC FILTERS
        # -----------------------------
        st.markdown("### Numeric filters")

        numeric_cols = out.select_dtypes(include="number").columns.tolist()
        binary_flag_col = "is_churned_historical"
        regular_numeric_cols = [c for c in numeric_cols if c != binary_flag_col]

        selected_numeric_filters = st.multiselect(
            "Choose numeric columns",
            options=regular_numeric_cols,
            default=[],
            help="Choose one or more numeric columns to filter.",
        )

        numeric_filter_config = {}

        for col in selected_numeric_filters:
            with st.expander(f"{col} filter", expanded=False):
                col_data = out[col].dropna()
                is_integer_like = pd.api.types.is_integer_dtype(out[col]) or (
                    not col_data.empty and (col_data % 1 == 0).all()
                )

                mode = st.selectbox(
                    f"{col} condition",
                    options=["between", ">=", "<=", "="],
                    key=f"{col}_mode",
                )

                if mode == "between":
                    c1, c2 = st.columns(2)
                    with c1:
                        min_val = st.number_input(
                            f"{col} min",
                            value=float(col_data.min()) if not col_data.empty else 0.0,
                            format="%d" if is_integer_like else "%.4f",
                            step=1 if is_integer_like else 0.01,
                            key=f"{col}_min",
                        )
                    with c2:
                        max_val = st.number_input(
                            f"{col} max",
                            value=float(col_data.max()) if not col_data.empty else 0.0,
                            format="%d" if is_integer_like else "%.4f",
                            step=1 if is_integer_like else 0.01,
                            key=f"{col}_max",
                        )
                    numeric_filter_config[col] = {"mode": "between", "min": min_val, "max": max_val}

                elif mode == ">=":
                    val = st.number_input(
                        f"{col} value",
                        value=float(col_data.min()) if not col_data.empty else 0.0,
                        format="%d" if is_integer_like else "%.4f",
                        step=1 if is_integer_like else 0.01,
                        key=f"{col}_gte",
                    )
                    numeric_filter_config[col] = {"mode": ">=", "value": val}

                elif mode == "<=":
                    val = st.number_input(
                        f"{col} value",
                        value=float(col_data.max()) if not col_data.empty else 0.0,
                        format="%d" if is_integer_like else "%.4f",
                        step=1 if is_integer_like else 0.01,
                        key=f"{col}_lte",
                    )
                    numeric_filter_config[col] = {"mode": "<=", "value": val}

                elif mode == "=":
                    val = st.number_input(
                        f"{col} value",
                        value=float(col_data.min()) if not col_data.empty else 0.0,
                        format="%d" if is_integer_like else "%.4f",
                        step=1 if is_integer_like else 0.01,
                        key=f"{col}_eq",
                    )
                    numeric_filter_config[col] = {"mode": "=", "value": val}

        churn_flag_values = []
        if binary_flag_col in out.columns:
            churn_flag_values = st.multiselect(
                "is_churned_historical",
                options=[0, 1],
                default=[0, 1],
                help="Binary flag only.",
            )

    # -----------------------------
    # APPLY FILTERS
    # -----------------------------
    if search_term:
        mask = pd.Series(False, index=out.index)
        for col in out.columns:
            mask = mask | out[col].astype(str).str.contains(search_term, case=False, na=False)
        out = out[mask]

    if status_filter:
        out = out[out["audit_action_status"].isin(status_filter)]

    for col, selected_values in categorical_filter_values.items():
        if selected_values:
            out = out[out[col].astype(str).isin(selected_values)]

    for col, rule in numeric_filter_config.items():
        if rule["mode"] == "between":
            low = min(rule["min"], rule["max"])
            high = max(rule["min"], rule["max"])
            out = out[out[col].between(low, high)]
        elif rule["mode"] == ">=":
            out = out[out[col] >= rule["value"]]
        elif rule["mode"] == "<=":
            out = out[out[col] <= rule["value"]]
        elif rule["mode"] == "=":
            out = out[out[col] == rule["value"]]

    if binary_flag_col in out.columns and churn_flag_values:
        out = out[out[binary_flag_col].isin(churn_flag_values)]

    return out

def _render_table(title: str, df: pd.DataFrame, key: str, app_user: str, db: DatabaseClient):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Editable audit state with direct save-back to PostgreSQL.</div>',
        unsafe_allow_html=True,
    )

    working_df = df.copy()

    bulk_col1, bulk_col2, bulk_col3 = st.columns([2, 2, 1])

    with bulk_col1:
        bulk_status = st.selectbox(
            f"Set audit status for all filtered rows — {title}",
            options=AUDIT_OPTIONS,
            index=0,
            key=f"bulk_status_{key}",
        )

    with bulk_col2:
        bulk_note = st.text_input(
            f"Bulk note — {title}",
            value="",
            key=f"bulk_note_{key}",
            placeholder="Optional note for all filtered rows",
        )

    with bulk_col3:
        apply_bulk = st.button(f"Apply to filtered rows", key=f"apply_bulk_{key}")

    if apply_bulk and not working_df.empty:
        working_df["audit_action_status"] = bulk_status
        working_df["audit_notes"] = bulk_note
        working_df["audit_override_by"] = app_user
        working_df["audit_override_at"] = pd.Timestamp.utcnow().tz_localize(None)
        saved = db.save_overrides(working_df)
        st.success(f"Bulk-applied audit status to {saved} filtered rows.")
        df = working_df.copy()

    edited = st.data_editor(
        df,
        key=key,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "audit_action_status": st.column_config.SelectboxColumn(
                "Audit / Override Status",
                options=AUDIT_OPTIONS,
                required=True,
            ),
            "audit_notes": st.column_config.TextColumn("Audit Notes", width="large"),
            "audit_override_by": st.column_config.TextColumn("Overridden By", default=app_user),
            "audit_override_at": st.column_config.DatetimeColumn("Override Time"),
        },
        disabled=[c for c in df.columns if c not in {"audit_action_status", "audit_notes", "audit_override_by", "audit_override_at"}],
    )

    if st.button(f"Save changes: {title}", key=f"save_{key}"):
        edited["audit_override_by"] = edited["audit_override_by"].replace("", app_user)
        edited["audit_override_at"] = edited["audit_override_at"].fillna(pd.Timestamp.utcnow().tz_localize(None))
        count = db.save_overrides(edited)
        st.success(f"Saved {count} updates.")

    return edited

def _build_logs(customers_df: pd.DataFrame, action_taken: str, fallback_status: str, request_id: str, automation_target: str, automation_response: dict, app_user: str, notes: str = ""):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = []
    for _, row in customers_df.iterrows():
        rows.append(
            {
                "audit_id": str(uuid.uuid4()),
                "user_account_id": row.get("user_account_id", "UNKNOWN"),
                "allocated_operational_tier": row.get("allocated_operational_tier", ""),
                "action_status": row.get("audit_action_status", fallback_status),
                "action_taken": action_taken,
                "action_notes": notes or row.get("audit_notes", ""),
                "triggered_by": app_user,
                "request_id": request_id,
                "automation_target": automation_target,
                "automation_response": automation_response,
                "status": "SUCCESS",
                "event_timestamp": now,
            }
        )
    return rows


def run_app():
    cfg = get_config()
    app_user = cfg["app"]["app_user"]
    app_title = cfg["app"]["app_title"]

    st.set_page_config(page_title=app_title, page_icon="🚨", layout="wide", initial_sidebar_state="expanded")
    _inject_css()

    db = DatabaseClient(cfg)
    automation = AutomationClient(cfg)

    try:
        raw_df = _prepare_df(db.load_predictions())
    except Exception as e:
        st.error(f"Database load failed: {e}")
        st.stop()

    filtered_df = _apply_filters(raw_df)

    stable_df = filtered_df[filtered_df["allocated_operational_tier"] == "STABLE_NO_ACTION"].copy()
    vip_df = filtered_df[filtered_df["allocated_operational_tier"] == "VIP_RED_ALERT"].copy()
    email_df = filtered_df[filtered_df["allocated_operational_tier"] == "AUTOMATED_LOW_COST_EMAIL"].copy()

    approved_vip_df = _only_approved(vip_df)
    approved_email_df = _only_approved(email_df)

    st.caption(f"Approved dispatch-ready rows -> VIP: {len(approved_vip_df):,} | Automated email: {len(approved_email_df):,}")

    st.markdown(f'<div class="hero"><h1>{app_title}</h1><p>Review operational tiers, override decisions, dispatch n8n workflows, and preserve a full audit trail.</p></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Stable</div><div class="metric-value">{len(stable_df):,}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">VIP Red Alert</div><div class="metric-value">{len(vip_df):,}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Automated Email</div><div class="metric-value">{len(email_df):,}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Loaded Rows</div><div class="metric-value">{len(filtered_df):,}</div></div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Automation actions</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Buttons below send structured payloads to n8n, including customer lists and log objects.</div>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        vip_notes = st.text_area("VIP dispatch notes", value="Send VIP Red-Alert customer list to Customer Success/Sales team for manual outreach.")
        if st.button("Send VIP red customers to CS/Sales"):
            if approved_vip_df.empty:
                st.warning("No APPROVED VIP red customers available in the current filtered view.")
            else:
                request_id = str(uuid.uuid4())
                payload = {
                    "event_type": "VIP_RED_DISPATCH",
                    "request_id": request_id,
                    "triggered_by": app_user,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "target_teams": ["CS", "SALES"],
                    "notes": vip_notes,
                    "customers": _json_safe_records(approved_vip_df),
                    "logs": [
                        {
                            "user_account_id": row.get("user_account_id", "UNKNOWN"),
                            "action_taken": "SLACK_DISPATCH_TO_SALES",
                            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "PENDING",
                        }
                        for _, row in approved_vip_df.iterrows()
                    ],
                }
                try:
                    result = automation.dispatch(payload)
                    logs = _build_logs(approved_vip_df, "SLACK_DISPATCH_TO_SALES", "ESCALATED_TO_SALES", request_id, result["url"], result["response"], app_user, vip_notes)
                    db.insert_audit_logs(logs)
                    st.success("VIP workflow sent successfully.")
                except Exception as e:
                    st.error(f"VIP dispatch failed: {e}")

    with a2:
        email_notes = st.text_area("Automated email notes", value="Trigger and share customer list with CS/Sales.")
        if st.button("Send Customer List"):
            if approved_email_df.empty:
                st.warning("No APPROVED automated-email customers available in the current filtered view.")
            else:
                request_id = str(uuid.uuid4())
                payload = {
                    "event_type": "AUTOMATED_EMAIL_DISPATCH",
                    "request_id": request_id,
                    "triggered_by": app_user,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "target_teams": ["CS", "SALES"],
                    "notes": email_notes,
                    "customers": _json_safe_records(approved_email_df),
                    "logs": [
                        {
                            "user_account_id": row.get("user_account_id", "UNKNOWN"),
                            "action_taken": "AI_EMAIL_AUTOMATION_TRIGGERED",
                            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "PENDING",
                        }
                        for _, row in approved_email_df.iterrows()
                    ],
                }
                try:
                    result = automation.dispatch(payload)
                    logs = _build_logs(approved_email_df, "AI_EMAIL_AUTOMATION_TRIGGERED", "EMAIL_AUTOMATION_QUEUED", request_id, result["url"], result["response"], app_user, email_notes)
                    db.insert_audit_logs(logs)
                    st.success("Automated email workflow sent successfully.")
                except Exception as e:
                    st.error(f"Automated email dispatch failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Stable customers", "VIP red customers", "Automated email", "Audit logs"])
    with tab1:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        _render_table("Stable / No Action", stable_df, "stable_table", app_user, db)
        st.markdown('</div>', unsafe_allow_html=True)
    with tab2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        _render_table("VIP Red Alert", vip_df, "vip_table", app_user, db)
        st.markdown('</div>', unsafe_allow_html=True)
    with tab3:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        _render_table("Automated Low Cost Email", email_df, "email_table", app_user, db)
        st.markdown('</div>', unsafe_allow_html=True)
    with tab4:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Recent audit trail</div>', unsafe_allow_html=True)
        try:
            logs = db.recent_logs(200)
            st.dataframe(logs, use_container_width=True, hide_index=True)
        except Exception as e:
            st.info(f"Could not load audit logs yet: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
