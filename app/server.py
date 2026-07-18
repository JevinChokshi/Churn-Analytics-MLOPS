import os
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.stats import skew
import shap

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR/"calibrated_xgboost_pipeline.joblib"


app = FastAPI(title="Churn Inference API", version="1.0.0")


class InferenceRequest(BaseModel):
    rows: List[Dict[str, Any]]


class TechnicalFrustrationIndex(BaseEstimator, TransformerMixin):
    def __init__(self, feature_weights: dict):
        self.feature_weights = feature_weights
        self.means_ = {}
        self.stds_ = {}

    def fit(self, X: pd.DataFrame, y=None):
        for feature in self.feature_weights.keys():
            self.means_[feature] = X[feature].mean()
            self.stds_[feature] = X[feature].std() + 1e-9
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_transformed = X.copy()
        tfi_array = np.zeros(len(X))

        for feature, weight in self.feature_weights.items():
            z_score = (X[feature] - self.means_[feature]) / self.stds_[feature]
            tfi_array += weight * z_score

        X_transformed["technical_frustration_index"] = tfi_array
        return X_transformed


def apply_skew_transform(df, cols, threshold=1.5):
    df_transformed = df.copy()
    dropped_cols = []

    for col in cols:
        if col in df.columns:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            s_score = skew(series)
            if s_score > threshold:
                df_transformed[f"{col}_log1p"] = np.log1p(df[col])
                dropped_cols.append(col)

    df_transformed.drop(columns=dropped_cols, inplace=True, errors="ignore")
    return df_transformed


def engineer_friction_features(df):
    fe_df = df.copy()

    fe_df["flag_severe_backend_latency"] = (fe_df["avg_api_wait_time_ms"] >= 1700).astype(int)
    fe_df["flag_poor_time_to_interactive"] = (fe_df["avg_time_to_interactive_ms"] >= 2000).astype(int)
    fe_df["flag_catastrophic_lcp"] = (fe_df["largest_contentful_paint_ms"] >= 5300).astype(int)

    fe_df["latency_degradation_ratio"] = fe_df["trailing_30d_avg_latency_ms"] / (fe_df["avg_api_wait_time_ms"] + 1e-5)

    fe_df["total_friction_breaches"] = (
        fe_df["flag_severe_backend_latency"] +
        fe_df["flag_poor_time_to_interactive"] +
        fe_df["flag_catastrophic_lcp"]
    )

    fe_df["flag_hard_invoice_failure"] = (fe_df["total_failed_invoices"] > 0).astype(int)

    conditions = [
        (fe_df["avg_rating"].isnull()),
        (fe_df["avg_rating"] >= 1.0) & (fe_df["avg_rating"] <= 2.5),
        (fe_df["avg_rating"] > 2.5) & (fe_df["avg_rating"] <= 4.0),
        (fe_df["avg_rating"] > 4.0) & (fe_df["avg_rating"] <= 5.0),
    ]
    choices = ["NO_RATING", "LOW_RATING", "MED_RATING", "HIGH_RATING"]
    fe_df["rating_bucket"] = np.select(conditions, choices, default="NO_RATING")
    fe_df["rating_bucket"] = fe_df["rating_bucket"].astype("category")

    med_rev = fe_df["total_revenue_contributed"].median()
    fe_df["flag_enterprise_high_touch_cushion"] = np.where(
        (fe_df["total_revenue_contributed"] > med_rev) & (fe_df["total_ticket_escalations"] > 0), 1, 0
    )

    cols_to_drop = [
        "avg_latency_ms",
        "avg_dom_load_time_ms",
        "avg_first_contentful_paint_ms",
        "avg_render_time",
        "avg_rating",
        "total_failed_invoices",
        "persona_cluster",
    ]
    fe_df = fe_df.drop(columns=[col for col in cols_to_drop if col in fe_df.columns], errors="ignore")
    return fe_df


def engineer_momentum_vectors(df: pd.DataFrame) -> pd.DataFrame:
    df_eng = df.copy()

    current_month_engagement = df_eng["trailing_7d_avg_active_minutes"] * 4
    historical_engagement = df_eng["avg_daily_active_minutes"] * 30

    df_eng["engagement_velocity_mom"] = np.where(
        historical_engagement == 0,
        0.0,
        (current_month_engagement - historical_engagement) / historical_engagement
    )

    total_lifetime_duration = df_eng["total_active_days_observed"] * df_eng["avg_daily_active_minutes"]
    total_actions = df_eng["total_clickstream_events"]

    df_eng["session_density"] = np.where(
        total_actions == 0,
        0.0,
        total_lifetime_duration / total_actions
    )

    density_10th_percentile = df_eng["session_density"].quantile(0.10)
    df_eng["is_frantic_user"] = (df_eng["session_density"] < density_10th_percentile).astype(int)
    df_eng["flag_rage_refresh_clicker"] = (df_eng["frequent_refresh_clicks"] > 0).astype(int)

    return df_eng


def sanitize_for_json(value):
    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if pd.isna(value):
        return None
    return value


@app.on_event("startup")
def load_artifacts():
    import __main__
    __main__.TechnicalFrustrationIndex = TechnicalFrustrationIndex

    global pipeline, model, encoder, tfi, low_card_cols
    global dropped_features, feature_order, eng_cols
    global base_tree, explainer

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")

    pipeline = joblib.load(MODEL_PATH)

    model = pipeline["model"]
    encoder = pipeline["encoder"]
    tfi = pipeline["tfi"]
    low_card_cols = pipeline["low_card_cols"]
    dropped_features = pipeline["dropped_features"]
    feature_order = pipeline["final_feature_order"]
    eng_cols = pipeline["eng_cols"]
    base_tree = pipeline["base_tree"]

    explainer = shap.TreeExplainer(base_tree)


def preprocess_and_predict(X_raw: pd.DataFrame) -> pd.DataFrame:
    X_raw = X_raw.copy()

    cols = X_raw.columns.tolist()
    for col in cols:
        if "lifetime_" in col:
            X_raw.rename(columns={col: col.replace("lifetime_", "")}, inplace=True)
    
    num_cols = ['user_account_id', 'avg_authentication_risk_score', 'avg_rating',
       'email_verification_flag', 'marketing_opt_in_flag',
       'onboarding_completed_flag', 'customer_tenure_days',
       'total_active_days_observed', 'total_login_attempts',
       'total_successful_logins', 'total_failed_logins',
       'total_manual_logouts', 'avg_daily_active_minutes',
       'total_clickstream_events', 'apply_filter_clicks', 'export_clicks',
       'frequent_refresh_clicks', 'subscription_settings_clicks',
       'submit_form_clicks', 'update_payment_method_clicks',
       'total_reports_run', 'total_projects_saved', 'home_screen_views',
       'billing_screen_views', 'report_screen_views', 'workspace_screen_views',
       'total_support_tickets', 'high_priority_tickets',
       'agent_replies_recieved', 'total_ticket_escalations',
       'total_invoices_generated', 'total_failed_invoices',
       'total_revenue_contributed', 'avg_latency_ms', 'avg_api_wait_time_ms',
       'avg_cumulative_layout_shift', 'avg_dom_load_time_ms',
       'avg_first_contentful_paint_ms', 'largest_contentful_paint_ms',
       'avg_render_time', 'avg_time_to_interactive_ms',
       'trailing_7d_avg_active_minutes', 'trailing_7d_total_logins',
       'trailing_7d_total_clicks', 'trailing_7d_support_tickets',
       'trailing_7d_active_open_tickets', 'trailing_30d_failed_payments_count',
       'trailing_30d_failed_logins_count', 'trailing_30d_avg_latency_ms',
       'active_minutes_drop_ratio_7d', 'login_frequency_drop_ratio_7d',
       'is_churned']
    
    for col in num_cols:
        X_raw[col] = pd.to_numeric(X_raw[col], errors="coerce")

    X = X_raw.copy()
    X = engineer_friction_features(X)
    X = engineer_momentum_vectors(X)
    X = apply_skew_transform(X, eng_cols)
    X.drop(columns=["user_account_id", "is_churned"], inplace=True, errors="ignore")

    X = tfi.transform(X)
    X = encoder.transform(X)

    X = pd.get_dummies(X, columns=low_card_cols, drop_first=True, dtype=float)
    X.drop(columns=dropped_features, inplace=True, errors="ignore")
    X = X.reindex(columns=feature_order, fill_value=0.0)

    X.columns = (
        X.columns.str.replace("[", "_", regex=False)
        .str.replace("]", "_", regex=False)
        .str.replace("<", "lt_", regex=False)
        .str.replace(">", "gt_", regex=False)
    )

    full_portfolio_probs = model.predict_proba(X)[:, 1]

    revenue_native = X_raw["total_revenue_contributed"].values
    full_tenures = X_raw["customer_tenure_days"].values
    currencies = X_raw["currency"].values

    full_arpus_native = (revenue_native / np.maximum(full_tenures, 1)) * 30
    full_ltvs_native = (full_arpus_native * 0.80) / (full_portfolio_probs + 1e-5)

    shap_values_full = explainer(X).values
    top_driver_indices = np.argmax(shap_values_full, axis=1)
    top_driver_features = X.columns[top_driver_indices]

    USER_RISK_THRESHOLD = 0.35

    regional_vip_thresholds = np.select(
        [
            currencies == "USD",
            currencies == "EUR",
            currencies == "GBP",
            currencies == "JPY",
            currencies == "INR",
        ],
        [
            600.0,
            550.0,
            500.0,
            90000.0,
            50000.0,
        ],
        default=600.0
    )

    is_high_risk = full_portfolio_probs >= USER_RISK_THRESHOLD
    is_vip = full_ltvs_native > regional_vip_thresholds

    conditions_full = [
        is_high_risk & is_vip,
        is_high_risk & ~is_vip,
        ~is_high_risk
    ]
    choices_full = ["VIP_RED_ALERT", "AUTOMATED_LOW_COST_EMAIL", "STABLE_NO_ACTION"]
    full_allocated_tiers = np.select(conditions_full, choices_full, default="STABLE_NO_ACTION")

    df_out = pd.DataFrame({
        "user_account_id": X_raw["user_account_id"],
        "country": X_raw.get("country"),
        "industry_type": X_raw.get("industry_type"),
        "registration_plan_code": X_raw.get("registration_plan_code"),
        "customer_tenure_days": X_raw["customer_tenure_days"],
        "is_churned_historical": X_raw["is_churned"] if "is_churned" in X_raw.columns else None,
        "calibrated_churn_probability": np.round(full_portfolio_probs, 4),
        "monthly_arpu": np.round(full_arpus_native, 2),
        "projected_ltv": np.round(full_ltvs_native, 2),
        "currency": currencies,
        "allocated_operational_tier": full_allocated_tiers,
        "primary_frustration_driver_vector": top_driver_features
    })

    return df_out


@app.get("/health")
def health():
    return {"status": "ok", "model_path": MODEL_PATH}


@app.post("/predict")
def predict(request: InferenceRequest):
    try:
        if not request.rows:
            raise HTTPException(status_code=400, detail="Request body 'rows' is empty")

        df = pd.DataFrame(request.rows)
        predicted_df = preprocess_and_predict(df)

        records = predicted_df.to_dict(orient="records")
        records = [
            {k: sanitize_for_json(v) for k, v in row.items()}
            for row in records
        ]

        return {
            "count": len(records),
            "predictions": records
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))