CREATE SCHEMA mart;

CREATE TABLE mart.dim_users AS
SELECT
user_account_id,
external_user_uuid,
country,
locale_code,
timezone,
company_name,
job_title,
industry_type,
employee_count_range,
annual_revenue_range,
account_status,
registration_source,
profile_theme,
email_verification_flag,
marketing_opt_in_flag,
onboarding_completed_flag,
COALESCE(subscription_id, 00000) AS subscription_id,
user_tier,
currency,
subscription_plan_code,
subscription_status,
billing_cycle,
COALESCE(auto_renew_flag, -1) AS auto_renew_flag,
pdf_generation_variant,
advance_search_elastic_variant,
device_models,
network_carrier,
avg_authentication_risk_score,
avg_rating,
account_creation_date,
account_update_date,
last_successful_login_at,
trial_start_date,
trial_end_date,
subscription_start_date,
subscription_end_date,
cancellation_request_date,
cancellation_reason_code,
cancellation_comment,
account_deletion_date,
account_deletion_flag
FROM int.user_profiles;

CREATE TABLE mart.fct_daily_user_snapshot AS
SELECT 
-- A. Primary Temporal & Entity Composite Keys
spine.activity_date,
spine.user_account_id,
spine.subscription_id,

-- B. True Historical Trait Tracking (Changes Over Time)
spine.subscription_status AS historical_subscription_status,
spine.subscription_plan_code AS historical_subscription_plan_code,
spine.billing_cycle AS historical_billing_cycle,

-- C. User Authentication & Session Engagement Logs
COALESCE(act.total_login_attempts, 0) AS daily_login_attempts,
COALESCE(act.successful_logins_count, 0) AS daily_successful_logins,
COALESCE(act.failed_logins_count, 0) AS daily_failed_logins,
COALESCE(act.sessions_created_count, 0) AS daily_sessions_created,
COALESCE(act.manual_logouts_count, 0) AS daily_manual_logouts,
COALESCE(act.total_duration_sec, 0.0) AS daily_total_duration_sec,

-- D. Geographical & Device Context Markers
COALESCE(act.total_devices_used, 0) AS daily_devices_active_count,
COALESCE(act.device_models, 'NONE') AS daily_device_models_used,
COALESCE(act.browsers_used, 'NONE') AS daily_browsers_used,
COALESCE(act.platform_types, 'NONE') AS daily_platform_types_used,
COALESCE(act.geo_city, 'UNKNOWN') AS daily_geo_city_location,

-- E. Feature Adoption, UI Telemetry & Click Logs
COALESCE(act.total_events, 0) AS daily_total_clickstream_events,
COALESCE(act.apply_filter_clicks, 0) AS daily_apply_filter_clicks,
COALESCE(act.click_export_clicks, 0) AS daily_click_export_clicks,
COALESCE(act.frequent_refresh_clicks, 0) AS daily_frequent_refresh_clicks,
COALESCE(act.open_subscription_settings_clicks, 0) AS daily_open_subscription_settings_clicks,
COALESCE(act.run_report_clicks, 0) AS daily_run_report_clicks,
COALESCE(act.save_project_clicks, 0) AS daily_save_project_clicks,
COALESCE(act.submit_form_clicks, 0) AS daily_submit_form_clicks,
COALESCE(act.update_payment_method_clicks, 0) AS daily_update_payment_method_clicks,

-- F. Screen Views / Navigation Pathways
COALESCE(act.home_screen_views, 0) AS daily_home_screen_views,
COALESCE(act.billing_screen_views, 0) AS daily_billing_screen_views,
COALESCE(act.report_screen_views, 0) AS daily_report_screen_views,
COALESCE(act.workspace_screen_views, 0) AS daily_workspace_screen_views,

-- G. Application Frontend Performance Benchmarks
COALESCE(act.avg_latency, 0.0) AS daily_avg_latency_ms,
COALESCE(act.avg_first_contentful_paint_ms, 0.0) AS daily_avg_first_contentful_paint_ms,
COALESCE(act.largest_contentful_paint_ms, 0.0) AS daily_largest_contentful_paint_ms,
COALESCE(act.avg_cumulative_layout_shift, 0.0) AS daily_avg_cumulative_layout_shift,
COALESCE(act.avg_time_to_interactive_ms, 0.0) AS daily_avg_time_to_interactive_ms,
COALESCE(act.avg_dom_load_time_ms, 0.0) AS daily_avg_dom_load_time_ms,
COALESCE(act.avg_api_wait_time_ms, 0.0) AS daily_avg_api_wait_time_ms,
COALESCE(act.avg_render_time_ms, 0.0) AS daily_avg_render_time_ms,

-- H. Support Ticket Escalations & Friction Markers
COALESCE(supp.tickets_opened_today, 0) AS daily_support_tickets_opened,
COALESCE(supp.high_priority_tickets_today, 0) AS daily_high_priority_tickets_opened,
COALESCE(supp.active_open_tickets_today, 0) AS daily_active_open_tickets_count,
COALESCE(supp.total_ticket_events_today, 0) AS daily_total_ticket_lifecycle_events,
COALESCE(supp.agent_replies_today, 0) AS daily_agent_replies_received,
COALESCE(supp.ticket_escalations_today, 0) AS daily_ticket_escalations_triggered,

-- I. Direct Daily Financial Revenue Ledger
COALESCE(bill.total_invoices_generated_today, 0) AS daily_invoices_generated,
COALESCE(bill.total_amount_invoiced_today, 0.0) AS daily_amount_invoiced,
COALESCE(bill.total_tax_invoiced_today, 0.0) AS daily_tax_invoiced,
COALESCE(bill.failed_invoices_today, 0) AS daily_failed_invoices_count,
COALESCE(bill.total_successful_payments_today, 0.0) AS daily_successful_payments_collected,
COALESCE(bill.has_payment_failure_today_flag, 0) AS daily_payment_failed_flag,
COALESCE(bill.payment_methods_used_today, 'NONE') AS daily_payment_methods_used,
COALESCE(bill.payment_failure_codes_today, 'NONE') AS daily_payment_failure_codes

FROM int.subscription_lifecycle_daily spine
-- Join behavioral tracking logs
LEFT JOIN int.user_activity_daily act 
ON spine.user_account_id = act.user_account_id 
AND spine.activity_date = act.activity_date
-- Join customer support logs
LEFT JOIN int.customer_support_daily supp 
ON spine.user_account_id = supp.user_account_id 
AND spine.activity_date = supp.activity_date
-- Join financial invoices and transaction log tracking
LEFT JOIN int.billing_and_revenue_daily bill 
ON spine.subscription_id = bill.subscription_id 
AND spine.activity_date = bill.activity_date;
