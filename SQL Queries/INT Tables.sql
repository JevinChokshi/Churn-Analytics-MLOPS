CREATE SCHEMA int;

CREATE TABLE int.user_profiles AS

WITH user_accounts AS (
SELECT 
user_account_id, 
external_user_uuid::uuid,
email_normalized, 
CASE WHEN email_verified_at IS NOT NULL THEN 1 ELSE 0 END AS email_verification_flag,
account_status_enum AS account_status,
registration_source,
locale_code,
timezone_name AS timezone,
CASE WHEN marketing_opt_in_flag THEN 1 ELSE 0 END AS marketing_opt_in_flag,
last_successful_login_at::date,
created_at::date AS account_creation_date,
updated_at::date AS account_update_date,
deleted_at::date AS account_deletion_date,
CASE WHEN is_deleted THEN 1 ELSE 0 END AS account_deletion_flag
FROM stg.app_user_accounts),

user_profiles AS (
SELECT
user_account_id,
display_name as user_name,
company_name,
job_title,
industry_code as industry_type,
employee_count_range,
annual_revenue_range,
phone_number,
country_code as country,
REGEXP_REPLACE(REGEXP_REPLACE(profile_attributes_json, '([a-zA-Z0-9_]+)\s*:', '"\1":', 'g'),':\s*([a-zA-Z0-9_]+)', ': "\1"', 'g')::json->>'theme' as profile_theme,
CASE WHEN REGEXP_REPLACE(REGEXP_REPLACE(profile_attributes_json, '([a-zA-Z0-9_]+)\s*:', '"\1":', 'g'),':\s*([a-zA-Z0-9_]+)', ': "\1"', 'g')::json->>'onboarding_completed' = 'true' THEN 1 ELSE 0 END as onboarding_completed_flag
FROM stg.app_user_profiles),


login_events AS(
SELECT
user_account_id,
COUNT(login_event_id) AS total_logins,
COUNT(CASE WHEN authentication_result = 'SUCCESS' THEN 1 END) AS successful_logins,
COUNT(CASE WHEN authentication_result = 'FAILURE' THEN 1 END) AS failed_logins,
ROUND(AVG(risk_score_raw::numeric), 3) AS avg_authentication_risk_score
FROM stg.auth_login_events
GROUP BY user_account_id),

auth_sessions AS(
SELECT
user_account_id,
COUNT(session_id) as total_auth_sessions,
COUNT(DISTINCT device_id) as device_count,
ROUND(EXTRACT(EPOCH FROM AVG(session_terminated_at::timestamp - session_started_at::timestamp)),2) as avg_auth_session_duration_sec
FROM stg.auth_session_tokens
GROUP BY user_account_id),

experiments AS(
SELECT
user_account_id,
COUNT(assignment_id) as total_assigned_experiments
FROM stg.experiment_assignments
GROUP BY user_account_id),

feature_flags AS (
SELECT
user_account_id,
MAX(REGEXP_REPLACE(REGEXP_REPLACE(exposure_context_json, '([a-zA-Z0-9_]+)\s*:', '"\1":', 'g'),':\s*([a-zA-Z0-9_]+)', ': "\1"', 'g')::json->>'user_tier') as user_tier,
MAX(CASE WHEN feature_flag_key = 'pdf-generation-v2' THEN variant_key END) AS pdf_generation_variant,
MAX(CASE WHEN feature_flag_key = 'advanced-search-elastic' THEN variant_key END) AS advance_search_elastic_variant
FROM stg.feature_flag_exposures
GROUP BY user_account_id),

app_events AS(
SELECT
user_account_id,
MAX(REGEXP_REPLACE(REGEXP_REPLACE(event_payload, '([a-zA-Z0-9_]+)\s*:', '"\1":', 'g'), ':\s*([^"}]+)\s*([,}])', ': "\1"\2', 'g')::json->>'network_carrier') AS network_carrier
FROM stg.mobile_application_events
GROUP BY user_account_id),


product_sessions AS (
SELECT
user_account_id,
Count(product_session_id) as total_product_sessions,
COUNT(DISTINCT anonymous_device_id) as device_count,
STRING_AGG(DISTINCT device_model, ', ') as device_models,
ROUND(EXTRACT(EPOCH FROM AVG(session_ended_at::timestamp - session_started_at::timestamp)), 2) as avg_product_session_duration_sec
FROM stg.product_sessions
GROUP BY user_account_id),


subscriptions AS (
SELECT
user_account_id,
subscription_id,
subscription_plan_code,
subscription_status,
billing_cycle,
trial_started_at::date AS trial_start_date,
trial_ends_at::date AS trial_end_date,
subscription_started_at::date AS subscription_start_date,
subscription_ended_at::date AS subscription_end_date,
CASE WHEN auto_renew_enabled THEN 1 ELSE 0 END AS auto_renew_flag,
cancellation_requested_at::date AS cancellation_request_date,
cancellation_reason_code,
cancellation_comment
FROM stg.subscription_accounts),

support_tickets AS(
SELECT
user_account_id,
COUNT(ticket_id) AS total_tickets,
COUNT(CASE WHEN ticket_status = 'CLOSED' THEN 1 END) AS closed_tickets,
COUNT(CASE WHEN ticket_status = 'OPEN' THEN 1 END) AS open_tickets
FROM stg.support_tickets
GROUP BY user_account_id),

feedback AS (
SELECT
user_account_id,
COUNT(feedback_id) AS total_feedbacks,
ROUND(AVG(rating_value),2) AS avg_rating
FROM stg.user_feedback_submissions
GROUP BY user_account_id)

SELECT 
ua.user_account_id,
ua.external_user_uuid,
up.user_name,
ua.email_normalized AS email,
up.phone_number, 
up.country,
ua.locale_code, 
ua.timezone,
up.company_name, 
up.job_title, 
up.industry_type, 
up.employee_count_range, 
up.annual_revenue_range,
ua.email_verification_flag, 
ua.account_status, 
ua.registration_source, 
ua.marketing_opt_in_flag,  
up.profile_theme, 
up.onboarding_completed_flag,
s.subscription_id, 
COALESCE(s.subscription_plan_code, 'UNSUBSCRIBED') AS subscription_plan_code, 
COALESCE(s.subscription_status, 'UNSUBSCRIBED') AS subscription_status,
COALESCE(s.billing_cycle, 'NA') AS billing_cycle, 
s.auto_renew_flag,
ff.user_tier,
mp.currency_code AS currency, 
e.total_assigned_experiments,
ff.pdf_generation_variant, 
ff.advance_search_elastic_variant,
le.total_logins, 
le.successful_logins,
le.failed_logins,
le.avg_authentication_risk_score,
as_sess.total_auth_sessions, 
as_sess.avg_auth_session_duration_sec, 
ps.device_count AS device_count,
ps.device_models, 
COALESCE(ae.network_carrier, 'Unknown') AS network_carrier,
COALESCE(st.total_tickets, 0) AS total_tickets, 
COALESCE(st.open_tickets, 0) AS open_tickets,
COALESCE(st.closed_tickets, 0) AS closed_tickets,
COALESCE(f.total_feedbacks, 0) AS total_feedbacks,
f.avg_rating,
ua.account_creation_date, 
ua.account_update_date, 
ua.last_successful_login_at, 
s.trial_start_date, 
s.trial_end_date, 
s.subscription_start_date, 
s.subscription_end_date, 
s.cancellation_request_date, 
COALESCE(s.cancellation_reason_code, 'NA') AS cancellation_reason_code,
COALESCE(s.cancellation_comment, 'NA') AS cancellation_comment,
ua.account_deletion_date, 
ua.account_deletion_flag

FROM user_accounts ua
LEFT JOIN user_profiles up ON ua.user_account_id = up.user_account_id
LEFT JOIN login_events le ON ua.user_account_id = le.user_account_id
LEFT JOIN auth_sessions as_sess ON ua.user_account_id = as_sess.user_account_id
LEFT JOIN experiments e ON ua.user_account_id = e.user_account_id
LEFT JOIN feature_flags ff ON ua.user_account_id = ff.user_account_id
LEFT JOIN app_events ae ON ua.user_account_id = ae.user_account_id
LEFT JOIN product_sessions ps ON ua.user_account_id = ps.user_account_id
LEFT JOIN subscriptions s ON ua.user_account_id = s.user_account_id
LEFT JOIN support_tickets st ON ua.user_account_id = st.user_account_id
LEFT JOIN feedback f ON ua.user_account_id = f.user_account_id
LEFT JOIN stg.user_master_profiles mp ON ua.user_account_id = mp.user_account_id;


CREATE TABLE int.subscription_lifecycle_daily AS

WITH date_spine AS(
SELECT date_day::DATE
FROM
generate_series((SELECT MIN(effective_at::date) FROM stg.subscription_state_history), CURRENT_DATE, '1 day'::interval) AS date_day),

state_intervals AS(
SELECT 
h.subscription_id,
a.user_account_id,
a.subscription_plan_code,
a.billing_cycle,
h.new_state AS subscription_status,
h.effective_at::date AS valid_from,
COALESCE(LEAD(h.effective_at::date) OVER (PARTITION BY h.subscription_id ORDER BY h.effective_at ASC, h.subscription_state_id ASC) - 1, CURRENT_DATE) AS valid_to
FROM stg.subscription_state_history h
JOIN stg.subscription_accounts a
ON h.subscription_id = a.subscription_id)

SELECT 
s.subscription_id,
s.user_account_id,
d.date_day AS activity_date,
s.subscription_plan_code,
s.billing_cycle,
s.subscription_status
FROM date_spine d
JOIN state_intervals s 
ON d.date_day BETWEEN s.valid_from AND s.valid_to
ORDER BY s.user_account_id, s.subscription_id, d.date_day;

CREATE TABLE int.user_activity_daily AS

WITH events_per_session AS (
SELECT
product_session_id,
COUNT(event_id) AS total_events,
COUNT(CASE WHEN event_name = 'apply_filter' THEN 1 END) AS apply_filter_count,
COUNT(CASE WHEN event_name = 'click_export' THEN 1 END) AS click_export_count,
COUNT(CASE WHEN event_name = 'frequent_refresh' THEN 1 END) AS frequent_refresh_count,
COUNT(CASE WHEN event_name = 'open_subscription_settings' THEN 1 END) AS open_subscription_settings_count,
COUNT(CASE WHEN event_name = 'run_report' THEN 1 END) AS run_report_count,
COUNT(CASE WHEN event_name = 'save_project' THEN 1 END) AS save_project_count,
COUNT(CASE WHEN event_name = 'submit_form' THEN 1 END) AS submit_form_count,
COUNT(CASE WHEN event_name = 'update_payment_method' THEN 1 END) AS update_payment_method_count,
COUNT(CASE WHEN page_screen_name = 'HOME' THEN 1 END) AS home_screen_views,
COUNT(CASE WHEN page_screen_name = 'BILLING' THEN 1 END) AS billing_screen_views,
COUNT(CASE WHEN page_screen_name = 'REPORTS' THEN 1 END) AS report_screen_views,
COUNT(CASE WHEN page_screen_name = 'WORKSPACE' THEN 1 END) AS workspace_screen_views,
ROUND(AVG(latency_ms), 0) AS avg_latency,
STRING_AGG(DISTINCT geo_city, ', ') as geo_city
FROM stg.clickstream_events
GROUP BY product_session_id
),

product_events AS (
SELECT
p.user_account_id,
p.created_at::date as activity_date,
SUM(EXTRACT(EPOCH FROM (p.session_ended_at::timestamp - p.session_started_at::timestamp))) AS total_duration_sec,
COUNT(DISTINCT p.device_model) AS total_devices_used,
STRING_AGG(DISTINCT p.device_model, ', ') AS device_models,
STRING_AGG(DISTINCT p.browser_name, ', ') AS browsers_used,
STRING_AGG(DISTINCT p.platform_type, ', ') AS platform_types,
STRING_AGG(DISTINCT f.network_type, ', ') AS network_type,
SUM(s.total_events) AS total_events,
SUM(s.apply_filter_count) AS apply_filter_clicks,
SUM(s.click_export_count) AS click_export_clicks,
SUM(s.frequent_refresh_count) AS frequent_refresh_clicks,
SUM(s.open_subscription_settings_count) AS open_subscription_settings_clicks,
SUM(s.run_report_count) AS run_report_clicks,
SUM(s.save_project_count) AS save_project_clicks,
SUM(s.submit_form_count) AS submit_form_clicks,
SUM(s.update_payment_method_count) AS update_payment_method_clicks,
SUM(s.home_screen_views) AS home_screen_views,
SUM(s.billing_screen_views) AS billing_screen_views,
SUM(s.report_screen_views) AS report_screen_views,
SUM(s.workspace_screen_views) AS workspace_screen_views,
ROUND(AVG(avg_latency::numeric), 0) AS avg_latency,
ROUND(AVG(f.first_contentful_paint_ms::numeric), 0) AS avg_first_contentful_paint_ms,
ROUND(MAX(f.largest_contentful_paint_ms::numeric), 0) AS largest_contentful_paint_ms,
ROUND(AVG(f.cumulative_layout_shift::numeric), 2) AS avg_cumulative_layout_shift,
ROUND(AVG(f.time_to_interactive_ms::numeric), 0) AS avg_time_to_interactive_ms,
ROUND(AVG(f.dom_load_time_ms::numeric), 0) AS avg_dom_load_time_ms,
ROUND(AVG(f.api_wait_time_ms::numeric), 0) AS avg_api_wait_time_ms,
ROUND(AVG(f.render_time_ms::numeric), 0) AS avg_render_time_ms,
MAX(s.geo_city) AS geo_city
FROM stg.product_sessions p
JOIN stg.frontend_performance_events f
ON p.product_session_id = f.product_session_id
JOIN events_per_session s ON p.product_session_id = s.product_session_id
GROUP BY user_account_id, created_at::date
),

daily_logins AS (
SELECT 
user_account_id,
created_at::date AS activity_date,
COUNT(login_event_id) AS total_login_attempts,
COUNT(CASE WHEN authentication_result = 'SUCCESS' THEN 1 END) AS successful_logins_count,
COUNT(CASE WHEN authentication_result = 'FAILURE' THEN 1 END) AS failed_logins_count,

-- Geolocation Fallback from Login Attempt
MAX(geo_city) AS login_geo_city,

-- Rule 1, 2, and 3 User Agent string decoding logic
STRING_AGG(DISTINCT (CASE 
WHEN user_agent_string LIKE '%Android%' THEN device_fingerprint_hash
WHEN user_agent_string LIKE '%iPhone%' THEN device_fingerprint_hash
WHEN user_agent_string LIKE '%Windows%' THEN device_fingerprint_hash
ELSE 'UNKNOWN_DEVICE'
END), ', ') AS login_device_models,

STRING_AGG(DISTINCT (CASE 
WHEN user_agent_string LIKE '%Android%' THEN device_fingerprint_hash
WHEN user_agent_string LIKE '%iPhone%' THEN device_fingerprint_hash
WHEN user_agent_string LIKE '%Windows%' THEN device_fingerprint_hash
ELSE 'UNKNOWN_BROWSER'
END), ', ') AS login_browsers_used,

STRING_AGG(DISTINCT (CASE 
WHEN user_agent_string LIKE '%Android%' THEN 'Android'
WHEN user_agent_string LIKE '%iPhone%' THEN 'IOS'
WHEN user_agent_string LIKE '%Windows%' THEN 'WEB'
ELSE 'UNKNOWN_PLATFORM'
END), ', ') AS login_platform_types

FROM stg.auth_login_events
GROUP BY user_account_id, created_at::date
),

daily_auth_sessions AS (
SELECT 
user_account_id,
session_started_at::date AS activity_date,
COUNT(session_id) AS sessions_created_count,
COUNT(CASE WHEN termination_reason = 'USER_LOGOUT' THEN 1 END) AS manual_logouts_count
FROM stg.auth_session_tokens
GROUP BY user_account_id, session_started_at::date
)


SELECT 
COALESCE(p.user_account_id, l.user_account_id, s.user_account_id) AS user_account_id,
COALESCE(p.activity_date, l.activity_date, s.activity_date) AS activity_date,
COALESCE(l.total_login_attempts, 0) AS total_login_attempts,
COALESCE(l.successful_logins_count, 0) AS successful_logins_count,
COALESCE(l.failed_logins_count, 0) AS failed_logins_count,
COALESCE(s.sessions_created_count, 0) AS sessions_created_count,
COALESCE(s.manual_logouts_count, 0) AS manual_logouts_count,
COALESCE(p.total_duration_sec, 0) AS total_duration_sec,
COALESCE(p.total_devices_used, 0) AS total_devices_used,
COALESCE(p.device_models, (SELECT device_model FROM stg.user_device_profiles WHERE device_id = l.login_device_models)) AS device_models,
COALESCE(p.browsers_used, (SELECT browser_name FROM stg.user_device_profiles WHERE device_id = l.login_browsers_used)) AS browsers_used,
COALESCE(p.platform_types, l.login_platform_types) AS platform_types,
COALESCE(p.geo_city, l.login_geo_city) AS geo_city,
COALESCE(p.total_events, 0) AS total_events,
COALESCE(p.apply_filter_clicks, 0) AS apply_filter_clicks,
COALESCE(p.click_export_clicks, 0) AS click_export_clicks,
COALESCE(p.frequent_refresh_clicks, 0) AS frequent_refresh_clicks,
COALESCE(p.open_subscription_settings_clicks, 0) AS open_subscription_settings_clicks,
COALESCE(p.run_report_clicks, 0) AS run_report_clicks,
COALESCE(p.save_project_clicks, 0) AS save_project_clicks,
COALESCE(p.submit_form_clicks, 0) AS submit_form_clicks,
COALESCE(p.update_payment_method_clicks, 0) AS update_payment_method_clicks,
COALESCE(p.home_screen_views, 0) AS home_screen_views,
COALESCE(p.billing_screen_views, 0) AS billing_screen_views,
COALESCE(p.report_screen_views, 0) AS report_screen_views,
COALESCE(p.workspace_screen_views, 0) AS workspace_screen_views,
COALESCE(p.avg_latency, 0) AS avg_latency,
COALESCE(p.avg_first_contentful_paint_ms, 0) AS avg_first_contentful_paint_ms,
COALESCE(p.largest_contentful_paint_ms, 0) AS largest_contentful_paint_ms,
COALESCE(p.avg_cumulative_layout_shift, 0) AS avg_cumulative_layout_shift,
COALESCE(p.avg_time_to_interactive_ms, 0) AS avg_time_to_interactive_ms,
COALESCE(p.avg_dom_load_time_ms, 0) AS avg_dom_load_time_ms,
COALESCE(p.avg_api_wait_time_ms, 0) AS avg_api_wait_time_ms,
COALESCE(p.avg_render_time_ms, 0) AS avg_render_time_ms


FROM product_events p
FULL OUTER JOIN daily_logins l
ON p.user_account_id = l.user_account_id 
AND p.activity_date = l.activity_date
FULL OUTER JOIN daily_auth_sessions s
ON COALESCE(p.user_account_id, l.user_account_id) = s.user_account_id 
AND COALESCE(p.activity_date, l.activity_date) = s.activity_date
ORDER BY user_account_id ASC, activity_date ASC;


CREATE TABLE int.customer_support_daily AS

WITH daily_ticket_base AS (
SELECT 
user_account_id,
created_at::date AS activity_date,
COUNT(ticket_id) AS tickets_opened_today,
COUNT(CASE WHEN ticket_priority = 'HIGH' THEN 1 END) AS high_priority_tickets_today,
COUNT(CASE WHEN ticket_status = 'OPEN' THEN 1 END) AS active_open_tickets_today
FROM stg.support_tickets
GROUP BY 1, 2
),

daily_ticket_events AS (
SELECT 
t.user_account_id,
e.created_at::date AS activity_date,
COUNT(e.ticket_event_id) AS total_ticket_events_today,
COUNT(CASE WHEN e.event_type = 'AGENT_COMMENT' THEN 1 END) AS agent_replies_today,
COUNT(CASE WHEN e.event_type = 'ESCALATION' THEN 1 END) AS ticket_escalations_today
FROM stg.support_ticket_events e
INNER JOIN stg.support_tickets t 
ON e.ticket_id = t.ticket_id -- The Bridge Join
GROUP BY 1, 2
)

SELECT 
COALESCE(b.user_account_id, e.user_account_id) AS user_account_id,
COALESCE(b.activity_date, e.activity_date) AS activity_date,

-- Ticket metrics
COALESCE(b.tickets_opened_today, 0) AS tickets_opened_today,
COALESCE(b.high_priority_tickets_today, 0) AS high_priority_tickets_today,
COALESCE(b.active_open_tickets_today, 0) AS active_open_tickets_today,

-- Event metrics
COALESCE(e.total_ticket_events_today, 0) AS total_ticket_events_today,
COALESCE(e.agent_replies_today, 0) AS agent_replies_today,
COALESCE(e.ticket_escalations_today, 0) AS ticket_escalations_today

FROM daily_ticket_base b
FULL OUTER JOIN daily_ticket_events e 
ON b.user_account_id = e.user_account_id 
AND b.activity_date = e.activity_date;


CREATE TABLE int.billing_and_revenue_daily AS

WITH aggregated_invoices_daily AS (
SELECT 
subscription_id AS user_id, 
created_at::date AS activity_date,
COUNT(invoice_id) AS total_invoices_generated_today,
SUM(total_amount) AS total_amount_invoiced_today,
SUM(tax_amount) AS total_tax_invoiced_today,
MAX(currency_code) AS currency,
COUNT(CASE WHEN invoice_status = 'FAILED' THEN 1 END) AS failed_invoices_today
FROM stg.billing_invoices
GROUP BY 1, 2
),

aggregated_payments_daily AS (
SELECT 
i.subscription_id AS user_id,
t.initiated_at::date AS activity_date,
SUM(CASE WHEN t.transaction_status = 'SUCCESS' THEN t.amount ELSE 0 END) AS total_successful_payments_today,
MAX(CASE WHEN t.transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS has_payment_failure_today_flag,
STRING_AGG(DISTINCT t.payment_method_type, ', ') AS payment_methods_used_today,
STRING_AGG(DISTINCT t.failure_code, ', ') AS payment_failure_codes_today
FROM stg.payment_transactions t
INNER JOIN stg.billing_invoices i 
ON t.invoice_id = i.invoice_id
GROUP BY 1, 2
)

SELECT 
COALESCE(inv.user_id, pmnt.user_id) AS subscription_id,
COALESCE(inv.activity_date, pmnt.activity_date) AS activity_date,
COALESCE(inv.total_invoices_generated_today, 0) AS total_invoices_generated_today,
COALESCE(inv.total_amount_invoiced_today, 0.0) AS total_amount_invoiced_today,
COALESCE(inv.total_tax_invoiced_today, 0.0) AS total_tax_invoiced_today,
COALESCE(inv.currency, '') AS currency,
COALESCE(inv.failed_invoices_today, 0) AS failed_invoices_today,
COALESCE(pmnt.total_successful_payments_today, 0.0) AS total_successful_payments_today,
COALESCE(pmnt.has_payment_failure_today_flag, 0) AS has_payment_failure_today_flag,
COALESCE(pmnt.payment_methods_used_today, 'NONE') AS payment_methods_used_today,
COALESCE(pmnt.payment_failure_codes_today, 'NONE') AS payment_failure_codes_today

FROM aggregated_invoices_daily inv
FULL OUTER JOIN aggregated_payments_daily pmnt
ON inv.user_id = pmnt.user_id 
AND inv.activity_date = pmnt.activity_date;
