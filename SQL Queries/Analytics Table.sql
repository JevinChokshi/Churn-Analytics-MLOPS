CREATE SCHEMA analytics;


CREATE TABLE analytics.churn_feature_matrix AS
WITH user_timeline_anchors AS (

SELECT 
user_account_id,
MIN(activity_date) AS first_active_date,
MAX(activity_date) AS final_active_date,

MAX(CASE WHEN historical_subscription_status = 'CANCELLED' THEN 1 ELSE 0 END) AS is_churned
FROM mart.fct_daily_user_snapshot
GROUP BY 1
),

behavioral_feature_engineering AS (

SELECT
f.user_account_id,


COUNT(DISTINCT f.activity_date) AS total_active_days_observed,
SUM(f.daily_login_attempts) AS lifetime_total_login_attempts,
SUM(f.daily_failed_logins) AS lifetime_total_failed_logins,
SUM(f.daily_manual_logouts) AS lifetime_total_manual_logouts,
SUM(f.daily_successful_logins) AS lifetime_total_successful_logins,
AVG(f.daily_total_duration_sec) / 60.0 AS lifetime_avg_daily_active_minutes,

SUM(f.daily_total_clickstream_events) AS lifetime_total_clickstream_events,
SUM(f.daily_apply_filter_clicks) AS lifetime_apply_filter_clicks,
SUM(f.daily_click_export_clicks) AS lifetime_export_clicks,
SUM(f.daily_frequent_refresh_clicks) AS lifetime_frequent_refresh_clicks,
SUM(f.daily_open_subscription_settings_clicks) AS lifetime_subscription_settings_clicks,
SUM(f.daily_submit_form_clicks) AS lifetime_submit_form_clicks,
SUM(f.daily_update_payment_method_clicks) AS lifetime_update_payment_method_clicks,
SUM(f.daily_run_report_clicks) AS lifetime_total_reports_run,
SUM(f.daily_save_project_clicks) AS lifetime_total_projects_saved,
SUM(f.daily_home_screen_views) AS lifetime_home_screen_views,
SUM(f.daily_billing_screen_views) AS lifetime_billing_screen_views,
SUM(f.daily_report_screen_views) AS lifetime_report_screen_views,
SUM(f.daily_workspace_screen_views) AS lifetime_workspace_screen_views,

SUM(f.daily_support_tickets_opened) AS lifetime_total_support_tickets,
SUM(f.daily_high_priority_tickets_opened) AS lifetime_high_priority_tickets,
SUM(f.daily_agent_replies_received) AS lifetime_agent_replies_recieved,
SUM(f.daily_ticket_escalations_triggered) AS lifetime_total_ticket_escalations,


SUM(f.daily_invoices_generated) AS lifetime_total_invoices_generated,
MAX(f.financial_transaction_currency) AS currency,
SUM(f.daily_successful_payments_collected) AS lifetime_total_revenue_contributed,
SUM(f.daily_failed_invoices_count) AS lifetime_total_failed_invoices,


AVG(f.daily_avg_latency_ms) AS lifetime_avg_latency_ms,
AVG(f.daily_avg_api_wait_time_ms) AS lifetime_avg_api_wait_time_ms,
AVG(f.daily_avg_cumulative_layout_shift) AS lifetime_avg_cumulative_layout_shift,
AVG(f.daily_avg_dom_load_time_ms) AS lifetime_avg_dom_load_time_ms,
AVG(f.daily_avg_first_contentful_paint_ms) AS lifetime_avg_first_contentful_paint_ms,
MAX(f.daily_largest_contentful_paint_ms) AS lifetime_largest_contentful_paint_ms,
AVG(f.daily_avg_render_time_ms) AS lifetime_avg_render_time_ms,
AVG(f.daily_avg_time_to_interactive_ms) AS lifetime_avg_time_to_interactive_ms,


AVG(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '7 days') 
THEN f.daily_total_duration_sec ELSE NULL END) / 60.0 AS trailing_7d_avg_active_minutes,
SUM(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '7 days') 
THEN f.daily_successful_logins ELSE 0 END) AS trailing_7d_total_logins,
SUM(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '7 days') 
THEN f.daily_total_clickstream_events ELSE 0 END) AS trailing_7d_total_clicks,
SUM(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '7 days') 
THEN f.daily_support_tickets_opened ELSE 0 END) AS trailing_7d_support_tickets,
SUM(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '7 days')
THEN f.daily_active_open_tickets_count ELSE 0 END) AS trailing_7d_active_open_tickets,


SUM(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '30 days') 
THEN f.daily_payment_failed_flag ELSE 0 END) AS trailing_30d_failed_payments_count,
SUM(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '30 days') 
THEN f.daily_failed_logins ELSE 0 END) AS trailing_30d_failed_logins_count,
AVG(CASE WHEN f.activity_date >= (a.final_active_date - INTERVAL '30 days') 
THEN f.daily_avg_latency_ms ELSE NULL END) AS trailing_30d_avg_latency_ms

FROM mart.fct_daily_user_snapshot f
INNER JOIN user_timeline_anchors a ON f.user_account_id = a.user_account_id
GROUP BY 1
)


SELECT
u.user_account_id,


u.country,
u.industry_type,
u.employee_count_range,
u.annual_revenue_range,
u.registration_source,
u.subscription_plan_code AS registration_plan_code,
u.billing_cycle AS registration_billing_cycle,
u.pdf_generation_variant,
u.advance_search_elastic_variant,
u.network_carrier,
u.avg_authentication_risk_score,
u.avg_rating,

u.email_verification_flag,
u.marketing_opt_in_flag,
u.onboarding_completed_flag,
(t.final_active_date - u.account_creation_date) AS customer_tenure_days,


COALESCE(h.total_active_days_observed, 0) AS lifetime_total_active_days_observed,
COALESCE(h.lifetime_total_login_attempts, 0) AS lifetime_total_login_attempts,
COALESCE(h.lifetime_total_successful_logins, 0) AS lifetime_total_successful_logins,
COALESCE(h.lifetime_total_failed_logins, 0) AS lifetime_total_failed_logins,
COALESCE(h.lifetime_total_manual_logouts, 0) AS lifetime_total_manual_logouts,
COALESCE(h.lifetime_avg_daily_active_minutes, 0.0) AS lifetime_avg_daily_active_minutes,

COALESCE(h.lifetime_total_clickstream_events, 0) AS lifetime_total_clickstream_events,
COALESCE(h.lifetime_apply_filter_clicks, 0) AS lifetime_apply_filter_clicks,
COALESCE(h.lifetime_export_clicks, 0) AS lifetime_export_clicks,
COALESCE(h.lifetime_frequent_refresh_clicks, 0) AS lifetime_frequent_refresh_clicks,
COALESCE(h.lifetime_subscription_settings_clicks, 0) AS lifetime_subscription_settings_clicks,
COALESCE(h.lifetime_submit_form_clicks, 0) AS lifetime_submit_form_clicks,
COALESCE(h.lifetime_update_payment_method_clicks, 0) AS lifetime_update_payment_method_clicks,
COALESCE(h.lifetime_total_reports_run, 0) AS lifetime_total_reports_run,
COALESCE(h.lifetime_total_projects_saved, 0) AS lifetime_total_projects_saved,
COALESCE(h.lifetime_home_screen_views, 0) AS lifetime_home_screen_views,
COALESCE(h.lifetime_billing_screen_views, 0) AS lifetime_billing_screen_views,
COALESCE(h.lifetime_report_screen_views, 0) AS lifetime_report_screen_views,
COALESCE(h.lifetime_workspace_screen_views, 0) AS lifetime_workspace_screen_views,

COALESCE(h.lifetime_total_support_tickets, 0) AS lifetime_total_support_tickets,
COALESCE(h.lifetime_high_priority_tickets, 0) AS lifetime_high_priority_tickets,
COALESCE(h.lifetime_agent_replies_recieved, 0) AS lifetime_agent_replies_recieved,
COALESCE(h.lifetime_total_ticket_escalations, 0) AS lifetime_total_ticket_escalations,

COALESCE(h.lifetime_total_invoices_generated, 0) AS lifetime_total_invoices_generated,
COALESCE(h.lifetime_total_failed_invoices, 0) AS lifetime_total_failed_invoices,
COALESCE(h.lifetime_total_revenue_contributed, 0.0) AS lifetime_total_revenue_contributed,
COALESCE(u.currency, 'UNKNOWN') AS currency,

COALESCE(h.lifetime_avg_latency_ms, 0.0) AS lifetime_avg_latency_ms,
COALESCE(h.lifetime_avg_api_wait_time_ms, 0.0) AS lifetime_avg_api_wait_time_ms,
COALESCE(h.lifetime_avg_cumulative_layout_shift, 0.0) AS lifetime_avg_cumulative_layout_shift,
COALESCE(h.lifetime_avg_dom_load_time_ms, 0.0) AS lifetime_avg_dom_load_time_ms,
COALESCE(h.lifetime_avg_first_contentful_paint_ms, 0.0) AS lifetime_avg_first_contentful_paint_ms,
COALESCE(h.lifetime_largest_contentful_paint_ms, 0.0) AS lifetime_largest_contentful_paint_ms,
COALESCE(h.lifetime_avg_render_time_ms, 0.0) AS lifetime_avg_render_time,
COALESCE(h.lifetime_avg_time_to_interactive_ms, 0.0) AS lifetime_avg_time_to_interactive_ms,


COALESCE(h.trailing_7d_avg_active_minutes, 0.0) AS trailing_7d_avg_active_minutes,
COALESCE(h.trailing_7d_total_logins, 0) AS trailing_7d_total_logins,
COALESCE(h.trailing_7d_total_clicks, 0) AS trailing_7d_total_clicks,
COALESCE(h.trailing_7d_support_tickets, 0) AS trailing_7d_support_tickets,
COALESCE(h.trailing_7d_active_open_tickets, 0) AS trailing_7d_active_open_tickets,
COALESCE(h.trailing_30d_failed_payments_count, 0) AS trailing_30d_failed_payments_count,
COALESCE(h.trailing_30d_failed_logins_count, 0) AS trailing_30d_failed_logins_count,
COALESCE(h.trailing_30d_avg_latency_ms, 0.0) AS trailing_30d_avg_latency_ms,


CASE 
WHEN COALESCE(h.lifetime_avg_daily_active_minutes, 0) = 0 THEN 0.0
ELSE COALESCE(h.trailing_7d_avg_active_minutes, 0.0) / h.lifetime_avg_daily_active_minutes 
END AS active_minutes_drop_ratio_7d,

CASE 
WHEN COALESCE(h.lifetime_total_successful_logins, 0) = 0 THEN 0.0
ELSE (COALESCE(h.trailing_7d_total_logins, 0.0) / 7.0) / (h.lifetime_total_successful_logins / h.total_active_days_observed)
END AS login_frequency_drop_ratio_7d,


t.is_churned

FROM mart.dim_users u
INNER JOIN user_timeline_anchors t ON u.user_account_id = t.user_account_id
INNER JOIN behavioral_feature_engineering h ON u.user_account_id = h.user_account_id;
