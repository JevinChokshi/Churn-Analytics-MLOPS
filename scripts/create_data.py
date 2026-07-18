import os
import json
import uuid
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

GLOBAL_SEED = 42
np.random.seed(GLOBAL_SEED)

START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
CURRENT_DATE = datetime(2026, 7, 7, tzinfo=timezone.utc)
NUM_USERS = 1000
skip_id = 0
OUTPUT_DIR = "data/raw"

NAME_POOLS = {
    "IN": {
        "first_names": ["kabir", "dev", "ayan", "reyansh", "vihaan", "amit", "suresh", "deepak", "tanvi", "diya", "ria", "kiara", "shruti", "payal", "manisha", "kritika", "alok", "vikram", "tanya", "simran"],
        "last_names": ["rao", "joshi", "shukla", "banerjee", "chatterjee", "shetty", "menon", "pillai", "malhotra", "kapoor", "das", "saxena", "bose", "pandey", "mukherjee"],
        "companies": ["zenith digital solutions", "maruti infotech", "tata labs pvt ltd", "vaibhav ventures", "indus data systems", "ayush pharma tech"],
        "jobs": ["systems analyst", "market research analyst", "frontend developer", "scrum master", "supply chain specialist", "clinical data coordinator"],
    },
    "US": {
        "first_names": ["william", "alexander", "henry", "samuel", "jackson", "charlotte", "amelia", "harper", "evelyn", "abigail", "lucas", "matthew", "emily", "madison"],
        "last_names": ["jackson", "white", "harris", "martin", "thompson", "garcia", "martinez", "robinson", "clark", "rodriguez"],
        "companies": ["summit cloud metrics", "atlantic tech partners", "vanguard data services", "apex retail group", "horizon health tech"],
        "jobs": ["business intelligence analyst", "growth marketing manager", "client experience specialist", "ux researcher", "devops lead"],
    },
    "GB": {
        "first_names": ["arthur", "muhammad", "oscar", "archie", "leo", "ella", "mia", "poppy", "ivy", "evie", "florence", "alice"],
        "last_names": ["johnson", "lewis", "robinson", "clarke", "hall", "wright", "king", "green", "baker", "edwards"],
        "companies": ["mersey digital ltd", "celtic analytics", "bristol insight group", "avvon retail labs"],
        "jobs": ["risk analyst", "commercial analyst", "brand manager", "client delivery executive", "cloud engineer"],
    },
    "DE": {
        "first_names": ["maximilian", "felix", "henry", "noah", "elias", "emma", "emilia", "hannah", "mila", "lina", "ella", "clara"],
        "last_names": ["koch", "bauer", "richter", "klein", "wolf", "schroder", "neumann", "schwarz", "zimmermann", "braun"],
        "companies": ["alpen data gmbh", "isar software lab", "hamburg metrics gmbh", "alpha logistik systeme"],
        "jobs": ["systemadministrator", "qualitatsmanager", "vertriebsleiter", "it consultant", "frontend entwickler"],
    },
    "JP": {
        "first_names": ["ituki", "toma", "asahi", "sora", "riku", "himari", "tsumugi", "ichika", "utano", "akari", "sara", "yuna"],
        "last_names": ["yamada", "maeda", "fujita", "ogawa", "goto", "hasegawa", "murakami", "kondo", "ishii", "saito"],
        "companies": ["fuji analytics kk", "heisei tech solutions", "edo digital labs", "yamato cloud systems"],
        "jobs": ["bi analyst", "localization specialist", "logistics coordinator", "backend engineer", "technical support engineer"],
    },
}



COUNTRY_CONFIG = {
    "IN": {
        "weight": 0.35,
        "locale": "en-IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "tax_rate": 0.18,
        "email_domains": [
            "gmail.com",
            "yahoo.in",
            "outlook.com",
            "icloud.com"
        ],
        "phone_prefix": "+91",
        "cities": [
            "Mumbai",
            "Delhi",
            "Bengaluru",
            "Hyderabad",
            "Chennai",
            "Pune"
        ],
        "regions": [
            "MH",
            "DL",
            "KA",
            "TS",
            "TN",
            "GJ"
        ],
        "providers": [
            "Jio",
            "Airtel",
            "Vi"
        ],
        "web_share": 0.56,
        "ios_share": 0.08,
        "android_share": 0.31,
        "partner_share": 0.05,
    },

    "US": {
        "weight": 0.25,
        "locale": "en-US",
        "timezone": "America/New_York",
        "currency": "USD",
        "tax_rate": 0.08,
        "email_domains": [
            "gmail.com",
            "outlook.com",
            "yahoo.com",
            "icloud.com"
        ],
        "phone_prefix": "+1",
        "cities": [
            "New York",
            "Los Angeles",
            "Chicago",
            "Seattle",
            "Austin",
            "Boston"
        ],
        "regions": [
            "NY",
            "CA",
            "IL",
            "WA",
            "TX",
            "MA"
        ],
        "providers": [
            "Verizon",
            "AT&T",
            "T-Mobile"
        ],
        "web_share": 0.60,
        "ios_share": 0.23,
        "android_share": 0.12,
        "partner_share": 0.05,
    },

    "GB": {
        "weight": 0.15,
        "locale": "en-GB",
        "timezone": "Europe/London",
        "currency": "GBP",
        "tax_rate": 0.20,
        "email_domains": [
            "gmail.com",
            "outlook.com",
            "hotmail.co.uk",
            "icloud.com"
        ],
        "phone_prefix": "+44",
        "cities": [
            "London",
            "Manchester",
            "Birmingham",
            "Liverpool",
            "Bristol"
        ],
        "regions": [
            "England",
            "Scotland",
            "Wales",
            "Northern Ireland"
        ],
        "providers": [
            "EE",
            "Vodafone UK",
            "O2"
        ],
        "web_share": 0.64,
        "ios_share": 0.18,
        "android_share": 0.13,
        "partner_share": 0.05,
    },

    "DE": {
        "weight": 0.15,
        "locale": "de-DE",
        "timezone": "Europe/Berlin",
        "currency": "EUR",
        "tax_rate": 0.19,
        "email_domains": [
            "gmail.com",
            "gmx.de",
            "web.de",
            "icloud.com"
        ],
        "phone_prefix": "+49",
        "cities": [
            "Berlin",
            "Munich",
            "Hamburg",
            "Frankfurt",
            "Cologne"
        ],
        "regions": [
            "Berlin",
            "Bavaria",
            "Hamburg",
            "Hesse",
            "North Rhine-Westphalia"
        ],
        "providers": [
            "Telekom",
            "Vodafone DE",
            "O2 Germany"
        ],
        "web_share": 0.66,
        "ios_share": 0.17,
        "android_share": 0.12,
        "partner_share": 0.05,
    },

    "JP": {
        "weight": 0.10,
        "locale": "ja-JP",
        "timezone": "Asia/Tokyo",
        "currency": "JPY",
        "tax_rate": 0.10,
        "email_domains": [
            "gmail.com",
            "yahoo.co.jp",
            "icloud.com",
            "outlook.jp"
        ],
        "phone_prefix": "+81",
        "cities": [
            "Tokyo",
            "Osaka",
            "Yokohama",
            "Nagoya",
            "Sapporo"
        ],
        "regions": [
            "Tokyo",
            "Osaka",
            "Kanagawa",
            "Aichi",
            "Hokkaido"
        ],
        "providers": [
            "NTT Docomo",
            "SoftBank",
            "au"
        ],
        "web_share": 0.57,
        "ios_share": 0.26,
        "android_share": 0.12,
        "partner_share": 0.05,
    },
}



PLAN_CONFIG = {
    "FREE": {
        "billing_cycle": "MONTHLY",
        "price": {
            "INR": 0.0,
            "USD": 0.0,
            "GBP": 0.0,
            "EUR": 0.0,
            "JPY": 0.0,
        },
    },

    "PRO_MONTHLY": {
        "billing_cycle": "MONTHLY",
        "price": {
            "INR": 1499.0,
            "USD": 29.0,
            "GBP": 24.0,
            "EUR": 27.0,
            "JPY": 4200.0,
        },
    },

    "PRO_YEARLY": {
        "billing_cycle": "YEARLY",
        "price": {
            "INR": 14999.0,
            "USD": 299.0,
            "GBP": 249.0,
            "EUR": 279.0,
            "JPY": 42000.0,
        },
    },

    "TEAM_MONTHLY": {
        "billing_cycle": "MONTHLY",
        "price": {
            "INR": 4999.0,
            "USD": 99.0,
            "GBP": 89.0,
            "EUR": 95.0,
            "JPY": 13900.0,
        },
    },

    "TEAM_YEARLY": {
        "billing_cycle": "YEARLY",
        "price": {
            "INR": 49999.0,
            "USD": 999.0,
            "GBP": 899.0,
            "EUR": 949.0,
            "JPY": 139000.0,
        },
    },

    "ENTERPRISE": {
        "billing_cycle": "YEARLY",
        "price": {
            "INR": 199999.0,
            "USD": 3999.0,
            "GBP": 3499.0,
            "EUR": 3799.0,
            "JPY": 560000.0,
        },
    },
}

INDUSTRIES = ["TECH", "FINANCE", "RETAIL", "HEALTHCARE", "EDTECH", "MANUFACTURING"]
EMPLOYEE_RANGES = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
REVENUE_RANGES = ["<1M", "1M-10M", "10M-50M", "50M+"]
ACTIVITY_TIERS = ["LIGHT", "REGULAR", "HEAVY", "POWER"]
ACTIVITY_WEIGHTS = [0.30, 0.42, 0.22, 0.06]


@dataclass
class DeviceProfile:
    platform_type: str
    operating_system: str
    device_model: str
    browser_name: str
    browser_version: str
    user_agent_string: str


def slugify_email(first_name: str, last_name: str) -> str:
    base = f"{first_name}.{last_name}".lower()
    allowed = []
    for ch in base:
        if ch.isascii() and (ch.isalnum() or ch in {'.', '_'}):
            allowed.append(ch)
    cleaned = ''.join(allowed).strip('._')
    return cleaned or f"user{np.random.randint(1000, 9999)}"


def make_uuid() -> str:
    return str(uuid.uuid4())


def random_dt_between(start_dt: datetime, end_dt: datetime) -> datetime:
    if end_dt <= start_dt:
        return start_dt
    delta = int((end_dt - start_dt).total_seconds())
    return start_dt + timedelta(seconds=int(np.random.randint(0, delta + 1)))


def random_dt_after(start_dt: datetime, min_minutes=0, max_days=1) -> datetime:
    max_seconds = max(min_minutes * 60, int(max_days * 86400))
    seconds = int(np.random.randint(min_minutes * 60, max_seconds + 1)) if max_seconds > 0 else 0
    return start_dt + timedelta(seconds=seconds)


def hash_token(*parts) -> str:
    return hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()


def random_public_ip() -> str:
    first = int(np.random.choice([23, 45, 52, 61, 78, 91, 103, 117, 141, 158, 172, 185, 203]))
    return f"{first}.{np.random.randint(0,255)}.{np.random.randint(0,255)}.{np.random.randint(1,255)}"


def build_phone(country_code: str) -> str:
    cfg = COUNTRY_CONFIG[country_code]
    if country_code == "IN":
        return cfg["phone_prefix"] + str(np.random.randint(6000000000, 9999999999, dtype=np.int64))
    if country_code == "US":
        return cfg["phone_prefix"] + str(np.random.randint(2010000000, 9899999999, dtype=np.int64))
    if country_code == "GB":
        return cfg["phone_prefix"] + str(np.random.randint(7400000000, 7999999999, dtype=np.int64))
    if country_code == "DE":
        return cfg["phone_prefix"] + str(np.random.randint(1500000000, 1799999999, dtype=np.int64))
    return cfg["phone_prefix"] + str(np.random.randint(700000000, 909999999, dtype=np.int64))


def pick_registration_source(country_code: str) -> str:
    cfg = COUNTRY_CONFIG[country_code]
    return np.random.choice(
        ["WEB", "IOS", "ANDROID", "PARTNER"],
        p=[cfg["web_share"], cfg["ios_share"], cfg["android_share"], cfg["partner_share"]],
    )


def build_device_pool(registration_source: str):
    web_devices = [
        DeviceProfile("WEB", "Windows 11", "Dell XPS 15", "Chrome", "126.0", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"),
        DeviceProfile("WEB", "Windows 11", "HP EliteBook", "Edge", "126.0", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/126.0"),
        DeviceProfile("WEB", "macOS 14", "MacBook Pro", "Safari", "17.5", "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) Safari/605.1.15"),
        DeviceProfile("WEB", "macOS 14", "MacBook Air", "Chrome", "126.0", "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) Chrome/126.0"),
    ]
    ios_devices = [
        DeviceProfile("IOS", "iOS 17", "iPhone 15", "Safari", "17.0", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"),
        DeviceProfile("IOS", "iOS 17", "iPhone 14", "Safari", "17.0", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15"),
    ]
    android_devices = [
        DeviceProfile("ANDROID", "Android 14", "Samsung Galaxy S24", "Chrome", "126.0", "Mozilla/5.0 (Linux; Android 14; SM-S921B) Chrome/126.0"),
        DeviceProfile("ANDROID", "Android 14", "OnePlus 12", "Chrome", "126.0", "Mozilla/5.0 (Linux; Android 14; CPH2581) Chrome/126.0"),
        DeviceProfile("ANDROID", "Android 14", "Pixel 8", "Chrome", "126.0", "Mozilla/5.0 (Linux; Android 14; Pixel 8) Chrome/126.0"),
    ]
    if registration_source == "IOS":
        return ios_devices + web_devices[:1]
    if registration_source == "ANDROID":
        return android_devices + web_devices[:1]
    return web_devices + ios_devices[:1] + android_devices[:1]


def sample_activity_params(tier: str):
    if tier == "LIGHT":
        return {"logins_per_active_day": (1, 1), "sessions_per_day": (1, 2), "active_day_prob": 0.18, "events_per_session": (2, 5)}
    if tier == "REGULAR":
        return {"logins_per_active_day": (1, 2), "sessions_per_day": (1, 3), "active_day_prob": 0.38, "events_per_session": (4, 8)}
    if tier == "HEAVY":
        return {"logins_per_active_day": (1, 3), "sessions_per_day": (2, 4), "active_day_prob": 0.60, "events_per_session": (6, 12)}
    return {"logins_per_active_day": (2, 4), "sessions_per_day": (3, 5), "active_day_prob": 0.78, "events_per_session": (8, 18)}


def determine_plan(employee_range: str, activity_tier: str) -> str:
    if employee_range in ["201-1000", "1000+"]:
        return np.random.choice(["TEAM_YEARLY", "ENTERPRISE", "PRO_MONTHLY"], p=[0.58, 0.26, 0.16])
    if employee_range == "51-200":
        return np.random.choice(["PRO_MONTHLY", "TEAM_YEARLY", "ENTERPRISE"], p=[0.52, 0.40, 0.08])
    if activity_tier == "POWER":
        return np.random.choice(["PRO_MONTHLY", "TEAM_YEARLY"], p=[0.35, 0.65])
    return np.random.choice(["PRO_MONTHLY", "TEAM_YEARLY"], p=[0.82, 0.18])


def daterange(start_date: datetime, end_date: datetime):
    current = start_date.date()
    end = end_date.date()
    while current <= end:
        yield current
        current += timedelta(days=1)


def generate_data(num_users=NUM_USERS, output_dir=OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)

    user_rows = []
    profile_rows = []
    master_rows = []
    device_rows = []

    country_codes = list(COUNTRY_CONFIG.keys())
    country_weights = [COUNTRY_CONFIG[c]["weight"] for c in country_codes]

    for i in range(skip_id+1, num_users + skip_id + 1):
        country_code = np.random.choice(country_codes, p=country_weights)
        cfg = COUNTRY_CONFIG[country_code]
        pools = NAME_POOLS[country_code]

        created_at = random_dt_between(START_DATE, CURRENT_DATE - timedelta(days=30))
        registration_source = pick_registration_source(country_code)
        first_name = np.random.choice(pools["first_names"])
        last_name = np.random.choice(pools["last_names"])
        display_name = f"{first_name} {last_name}"
        email_local = slugify_email(first_name, last_name)
        if np.random.rand() < 0.28:
            email_local = f"{email_local}{np.random.randint(1, 99)}"
        email_address = f"{email_local}@{np.random.choice(cfg['email_domains'])}"
        activity_tier = np.random.choice(ACTIVITY_TIERS, p=ACTIVITY_WEIGHTS)
        city = np.random.choice(cfg["cities"])
        region = np.random.choice(cfg["regions"])
        industry = np.random.choice(INDUSTRIES, p=[0.28, 0.12, 0.18, 0.14, 0.12, 0.16])
        employee_range = np.random.choice(EMPLOYEE_RANGES, p=[0.36, 0.30, 0.20, 0.10, 0.04])
        revenue_range = np.random.choice(REVENUE_RANGES, p=[0.34, 0.38, 0.18, 0.10])
        marketing_opt_in = bool(np.random.rand() < (0.46 if registration_source in ["WEB", "IOS"] else 0.35))
        account_status = np.random.choice(["ACTIVE", "SUSPENDED", "DELETED"], p=[0.955, 0.025, 0.020])
        deleted_at = pd.NaT
        is_deleted = False
        if account_status == "DELETED":
            deleted_at = random_dt_between(created_at + timedelta(days=7), min(CURRENT_DATE, created_at + timedelta(days=500)))
            is_deleted = True

        base_login = random_dt_between(created_at + timedelta(minutes=5), min(CURRENT_DATE, created_at + timedelta(days=20)))
        if pd.notna(deleted_at):
            base_login = min(base_login, deleted_at - timedelta(hours=1))

        phone_number = build_phone(country_code) if np.random.rand() < 0.82 else None
        company_name = np.random.choice(pools["companies"])
        job_title = np.random.choice(pools["jobs"])
        profile_json = json.dumps(
            {
                "theme": np.random.choice(["light", "dark", "system"], p=[0.15, 0.35, 0.50]),
                "onboarding_completed": bool(np.random.rand() < 0.88),
            }
        )

        user_account_id = i
        # workspace_id = 1000 + i
        external_user_uuid = make_uuid()

        device_pool = build_device_pool(registration_source)
        device_count = np.random.choice([1, 2, 3], p=[0.62, 0.28, 0.10])
        chosen_devices = list(np.random.choice(device_pool, size=device_count, replace=False if device_count <= len(device_pool) else True))
        provider = np.random.choice(cfg["providers"])

        user_rows.append(
            {
                "user_account_id": user_account_id,
                # "primary_workspace_id": workspace_id,
                "external_user_uuid": external_user_uuid,
                "email_address": email_address,
                "email_normalized": email_address.lower(),
                "email_verified_at": random_dt_after(created_at, min_minutes=10, max_days=2),
                "password_hash": "$2a$12$R9h/cIPz0gi.URNNX3rubedAK0ReQxc/ZG3.cQ./K.b",
                "password_algorithm": "bcrypt",
                "account_status_enum": account_status,
                "registration_source": registration_source,
                "locale_code": cfg["locale"],
                "timezone_name": cfg["timezone"],
                "marketing_opt_in_flag": marketing_opt_in,
                "gdpr_consent_version": "v3.0",
                "last_successful_login_at": base_login,
                "created_at": created_at,
                "updated_at": max(created_at, base_login),
                "deleted_at": deleted_at,
                "row_version_id": np.random.randint(1, 15),
                "is_deleted": is_deleted,
            }
        )

        profile_rows.append(
            {
                "profile_id": user_account_id,
                "user_account_id": user_account_id,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
                "company_name": company_name,
                "job_title": job_title,
                "industry_code": industry,
                "employee_count_range": employee_range,
                "annual_revenue_range": revenue_range,
                "phone_number": phone_number,
                "country_code": country_code,
                "profile_attributes_json": profile_json,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

        master_rows.append(
            {
                "user_account_id": user_account_id,
                "country_code": country_code,
                "city": city,
                "region": region,
                "currency_code": cfg["currency"],
                "tax_rate": cfg["tax_rate"],
                "activity_tier": activity_tier,
                "registration_source": registration_source,
                "carrier_provider": provider,
                "account_end_at": deleted_at if pd.notna(deleted_at) else CURRENT_DATE,
            }
        )

        for d_idx, device in enumerate(chosen_devices, start=1):
            device_rows.append(
                {
                    "user_account_id": user_account_id,
                    "device_rank": d_idx,
                    "device_id": hash_token(user_account_id, d_idx, device.device_model)[:32],
                    "platform_type": device.platform_type,
                    "operating_system": device.operating_system,
                    "device_model": device.device_model,
                    "browser_name": device.browser_name,
                    "browser_version": device.browser_version,
                    "user_agent_string": device.user_agent_string,
                    "country_code": country_code,
                    "geo_city": city,
                }
            )

    app_user_accounts = pd.DataFrame(user_rows)
    app_user_profiles = pd.DataFrame(profile_rows)
    user_master = pd.DataFrame(master_rows)
    user_device_profiles = pd.DataFrame(device_rows)

    subscriptions = []
    sub_states = []
    sub_id_seq = 10001

    for row in user_master.itertuples(index=False):
        user_account = app_user_accounts.loc[app_user_accounts.user_account_id == row.user_account_id].iloc[0]
        if user_account.account_status_enum == "DELETED" and np.random.rand() < 0.35:
            continue

        subscribe_prob = 0.90 if row.activity_tier in ["HEAVY", "POWER"] else 0.74 if row.activity_tier == "REGULAR" else 0.52
        if np.random.rand() > subscribe_prob:
            continue

        profile = app_user_profiles.loc[app_user_profiles.user_account_id == row.user_account_id].iloc[0]
        plan_code = determine_plan(profile.employee_count_range, row.activity_tier)
        billing_cycle = PLAN_CONFIG[plan_code]["billing_cycle"]
        trial_started_at = random_dt_after(user_account.created_at, min_minutes=20, max_days=3)
        trial_ends_at = trial_started_at + timedelta(days=14)
        subscription_started_at = trial_ends_at
        status = np.random.choice(["ACTIVE", "CANCELLED", "TRIAL", "PAUSED"], p=[0.69, 0.18, 0.06, 0.07])
        cancellation_reason = None
        cancellation_comment = None
        cancellation_requested_at = pd.NaT
        subscription_ended_at = pd.NaT
        auto_renew = True

        hard_end = row.account_end_at if pd.notna(row.account_end_at) else CURRENT_DATE
        if status == "TRIAL" and trial_ends_at < CURRENT_DATE - timedelta(days=7):
            status = "ACTIVE"

        if status == "CANCELLED":
            earliest = subscription_started_at + timedelta(days=30)
            latest = min(hard_end, CURRENT_DATE)
            if latest <= earliest:
                status = "ACTIVE"
            else:
                subscription_ended_at = random_dt_between(earliest, latest)
                cancellation_requested_at = subscription_ended_at - timedelta(hours=np.random.randint(3, 72))
                cancellation_reason = np.random.choice(
                    ["TOO_EXPENSIVE", "MISSING_FEATURES", "POOR_PERFORMANCE", "SWITCHED_COMPETITOR", "PROJECT_ENDED"],
                    p=[0.27, 0.18, 0.20, 0.15, 0.20],
                )
                cancellation_comment = {
                    "TOO_EXPENSIVE": "Budget constraints after trial conversion.",
                    "MISSING_FEATURES": "Needed workflow features were not available.",
                    "POOR_PERFORMANCE": "Slow page loads affected daily work.",
                    "SWITCHED_COMPETITOR": "Moved team to another vendor.",
                    "PROJECT_ENDED": "Internal project completed.",
                }[cancellation_reason]
                auto_renew = False

        if status == "PAUSED":
            auto_renew = False

        subscriptions.append(
            {
                "subscription_id": sub_id_seq,
                "user_account_id": row.user_account_id,
                "external_billing_customer_id": f"cus_{uuid.uuid4().hex[:14]}",
                "subscription_plan_code": plan_code,
                "subscription_status": status,
                "billing_cycle": billing_cycle,
                "trial_started_at": trial_started_at,
                "trial_ends_at": trial_ends_at,
                "subscription_started_at": subscription_started_at,
                "subscription_ended_at": subscription_ended_at,
                "auto_renew_enabled": auto_renew,
                "cancellation_requested_at": cancellation_requested_at,
                "cancellation_reason_code": cancellation_reason,
                "cancellation_comment": cancellation_comment,
                "created_at": trial_started_at,
                "updated_at": subscription_ended_at if pd.notna(subscription_ended_at) else max(subscription_started_at, user_account.updated_at),
            }
        )

        sub_states.append(
            {
                "subscription_state_id": len(sub_states) + 1,
                "subscription_id": sub_id_seq,
                "previous_state": "INITIAL",
                "new_state": "TRIAL",
                "transition_trigger": "USER_ACTION",
                "actor_user_id": row.user_account_id,
                "raw_transition_payload": json.dumps({"source": user_account.registration_source.lower()}),
                "effective_at": trial_started_at,
                "created_at": trial_started_at,
            }
        )

        if status != "TRIAL":
            sub_states.append(
                {
                    "subscription_state_id": len(sub_states) + 1,
                    "subscription_id": sub_id_seq,
                    "previous_state": "TRIAL",
                    "new_state": "ACTIVE",
                    "transition_trigger": "PAYMENT_SUCCESS",
                    "actor_user_id": -1,
                    "raw_transition_payload": json.dumps({"auto_bill": True}),
                    "effective_at": subscription_started_at,
                    "created_at": subscription_started_at,
                }
            )

        if status == "CANCELLED":
            sub_states.append(
                {
                    "subscription_state_id": len(sub_states) + 1,
                    "subscription_id": sub_id_seq,
                    "previous_state": "ACTIVE",
                    "new_state": "CANCELLED",
                    "transition_trigger": "USER_ACTION",
                    "actor_user_id": row.user_account_id,
                    "raw_transition_payload": json.dumps({"reason": cancellation_reason}),
                    "effective_at": subscription_ended_at,
                    "created_at": subscription_ended_at,
                }
            )

        if status == "PAUSED":
            pause_at = min(CURRENT_DATE, subscription_started_at + timedelta(days=np.random.randint(40, 180)))
            sub_states.append(
                {
                    "subscription_state_id": len(sub_states) + 1,
                    "subscription_id": sub_id_seq,
                    "previous_state": "ACTIVE",
                    "new_state": "PAUSED",
                    "transition_trigger": "USER_ACTION",
                    "actor_user_id": row.user_account_id,
                    "raw_transition_payload": json.dumps({"source": "billing_settings"}),
                    "effective_at": pause_at,
                    "created_at": pause_at,
                }
            )

        sub_id_seq += 1

    subscription_accounts = pd.DataFrame(subscriptions)
    subscription_state_history = pd.DataFrame(sub_states).sort_values(["subscription_id", "effective_at"]).reset_index(drop=True)
    if not subscription_state_history.empty:
        subscription_state_history["subscription_state_id"] = np.arange(1, len(subscription_state_history) + 1)

    subscription_lookup = subscription_accounts.set_index("user_account_id") if not subscription_accounts.empty else pd.DataFrame()
    master_lookup = user_master.set_index("user_account_id")
    profile_lookup = app_user_profiles.set_index("user_account_id")
    account_lookup = app_user_accounts.set_index("user_account_id")
    user_devices_lookup = {uid: grp.to_dict("records") for uid, grp in user_device_profiles.groupby("user_account_id")}

    login_rows = []
    session_rows = []
    product_session_rows = []
    perf_rows = []
    click_rows = []
    error_rows = []
    mobile_rows = []
    feature_rows = []
    experiment_rows = []
    feedback_rows = []
    notifications = []
    support_rows = []
    support_event_rows = []
    invoice_rows = []
    payment_rows = []

    login_id = 1
    perf_id = 200001
    click_id = 9000001
    error_id = 400001
    mobile_id = 1200001
    feature_id = 1300001
    experiment_id = 1400001
    feedback_id = 1500001
    notif_id = 800001
    ticket_id = 300001
    ticket_event_id = 700001
    invoice_id = 100001
    payment_id = 500001

    for uid in app_user_accounts["user_account_id"]:
        acct = account_lookup.loc[uid]
        master = master_lookup.loc[uid]
        devices = user_devices_lookup[uid]
        params = sample_activity_params(master.activity_tier)
        account_end = master.account_end_at if pd.notna(master.account_end_at) else CURRENT_DATE
        active_days = []

        for d in daterange(acct.created_at, min(account_end, CURRENT_DATE)):
            weekday_bonus = 0.06 if d.weekday() < 5 else -0.05
            age_days = (d - acct.created_at.date()).days
            early_bonus = 0.08 if age_days < 21 else 0.0
            active_prob = min(0.95, max(0.02, params["active_day_prob"] + weekday_bonus + early_bonus))
            if np.random.rand() < active_prob:
                active_days.append(d)

        if not active_days:
            active_days = [acct.created_at.date()]

        frustrated_user = False
        sub = None
        if uid in subscription_lookup.index:
            sub = subscription_lookup.loc[uid]
            frustrated_user = sub.cancellation_reason_code == "POOR_PERFORMANCE"

        for d in active_days:
            login_num = np.random.randint(params["logins_per_active_day"][0], params["logins_per_active_day"][1] + 1)
            for _ in range(login_num):
                device = devices[np.random.randint(0, len(devices))]
                login_time = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
                    hours=int(np.random.randint(6, 23)),
                    minutes=int(np.random.randint(0, 60)),
                    seconds=int(np.random.randint(0, 60)),
                )
                if login_time < acct.created_at or login_time > account_end:
                    continue

                result = np.random.choice(["SUCCESS", "FAILURE"], p=[0.91, 0.09])
                failure_reason = None
                risk = round(float(np.random.beta(1.4, 9.0)), 4)
                if result == "FAILURE":
                    failure_reason = np.random.choice(["INVALID_CREDENTIALS", "ACCOUNT_LOCKED", "MFA_FAILED", "TOKEN_EXPIRED"], p=[0.72, 0.07, 0.16, 0.05])
                    risk = round(min(1.0, risk + np.random.uniform(0.08, 0.22)), 4)

                login_rows.append(
                    {
                        "login_event_id": login_id,
                        "user_account_id": uid,
                        "login_method": np.random.choice(["PASSWORD", "SSO", "MAGIC_LINK"], p=[0.68, 0.22, 0.10]),
                        "authentication_result": result,
                        "client_ip_address": random_public_ip(),
                        "user_agent_string": device["user_agent_string"],
                        "device_fingerprint_hash": device["device_id"],
                        "geo_country": master.country_code,
                        "geo_city": master.city,
                        "failure_reason_code": failure_reason,
                        "risk_score_raw": risk,
                        "created_at": login_time,
                    }
                )
                current_login_id = login_id
                login_id += 1

                if result != "SUCCESS":
                    continue

                session_count = np.random.randint(params["sessions_per_day"][0], params["sessions_per_day"][1] + 1)
                for s_idx in range(session_count):
                    start_offset = np.random.randint(0, 180) if s_idx == 0 else np.random.randint(15, 220)
                    session_start = login_time + timedelta(minutes=int(start_offset))
                    if session_start > account_end:
                        continue

                    duration_minutes = np.random.randint(8, 75)
                    if master.activity_tier in ["HEAVY", "POWER"]:
                        duration_minutes += np.random.randint(15, 90)
                    if frustrated_user and np.random.rand() < 0.45:
                        duration_minutes = max(4, duration_minutes - np.random.randint(0, 30))
                    session_end = min(session_start + timedelta(minutes=int(duration_minutes)), account_end)
                    session_id = make_uuid()
                    termination_reason = np.random.choice(["USER_LOGOUT", "TIMEOUT", "SYSTEM_EVICTION"], p=[0.44, 0.51, 0.05])

                    session_rows.append(
                        {
                            "session_id": session_id,
                            "user_account_id": uid,
                            "access_token_hash": hash_token(session_id, "access")[:64],
                            "refresh_token_hash": hash_token(session_id, "refresh")[:64],
                            "device_id": device["device_id"],
                            "client_ip_address": login_rows[-1]["client_ip_address"],
                            "user_agent_string": device["user_agent_string"],
                            "session_started_at": session_start,
                            "session_expires_at": session_start + timedelta(hours=24),
                            "session_terminated_at": session_end,
                            "termination_reason": termination_reason,
                            "created_at": session_start,
                        }
                    )

                    product_session_rows.append(
                        {
                            "product_session_id": session_id,
                            "user_account_id": uid,
                            "anonymous_device_id": device["device_id"],
                            "platform_type": device["platform_type"],
                            "app_version": np.random.choice(["v3.4.2", "v3.5.0", "v3.5.1"], p=[0.20, 0.55, 0.25]),
                            "operating_system": device["operating_system"],
                            "device_model": device["device_model"],
                            "browser_name": device["browser_name"],
                            "browser_version": device["browser_version"],
                            "session_started_at": session_start,
                            "session_ended_at": session_end,
                            "termination_reason": termination_reason,
                            "created_at": session_start,
                        }
                    )

                    route = np.random.choice(["/dashboard/home", "/analytics/reports", "/settings/billing", "/projects/workspace"], p=[0.40, 0.25, 0.15, 0.20])
                    if frustrated_user:
                        fcp = int(np.clip(np.random.normal(2200, 450), 300, 9000))
                        lcp = int(np.clip(fcp + np.random.normal(1300, 300), 800, 15000))
                        api_wait = int(np.clip(np.random.lognormal(8.0, 0.35), 350, 20000))
                    else:
                        fcp = int(np.clip(np.random.normal(850, 160), 120, 3000))
                        lcp = int(np.clip(fcp + np.random.normal(420, 110), 250, 5000))
                        api_wait = int(np.clip(np.random.lognormal(5.4, 0.35), 40, 4000))

                    perf_rows.append(
                        {
                            "performance_event_id": perf_id,
                            "product_session_id": session_id,
                            "page_route": route,
                            "first_contentful_paint_ms": fcp,
                            "largest_contentful_paint_ms": lcp,
                            "cumulative_layout_shift": round(float(np.random.beta(2, 18)), 4),
                            "time_to_interactive_ms": int(lcp + np.random.randint(120, 450)),
                            "dom_load_time_ms": int(fcp + np.random.randint(90, 220)),
                            "api_wait_time_ms": api_wait,
                            "render_time_ms": int(np.random.randint(50, 650)),
                            "network_type": np.random.choice(["WIFI", "4G", "5G", "ETHERNET"], p=[0.46, 0.20, 0.24, 0.10]),
                            "captured_at": session_start,
                        }
                    )

                    if api_wait > 5000 and np.random.rand() < 0.40:
                        err_time = min(session_end, session_start + timedelta(minutes=np.random.randint(1, max(2, duration_minutes))))
                        error_rows.append(
                            {
                                "error_log_id": error_id,
                                "service_name": "api-gateway-service",
                                "service_version": "v2.1.0",
                                "environment_name": "PROD",
                                "trace_id": uuid.uuid4().hex,
                                "span_id": uuid.uuid4().hex[:16],
                                "exception_class": np.random.choice(["GatewayTimeoutException", "InternalServerError", "DatabaseDeadlockException"], p=[0.62, 0.27, 0.11]),
                                "error_message": "HTTP 504: The upstream microservice failed to respond within SLA.",
                                "stack_trace": "at com.enterprise.engine.GatewayFilter.lambda$apply$0(GatewayFilter.java:104)",
                                "http_status_code": 504,
                                "endpoint_path": "/v2/analytics/compute-aggregates",
                                "raw_error_payload": json.dumps({"timeout_threshold_ms": 5000}),
                                "occurred_at": err_time,
                            }
                        )
                        error_id += 1

                    perf_id += 1

                    event_min, event_max = params["events_per_session"]
                    event_count = np.random.randint(event_min, event_max + 1)
                    total_seconds = max(60, int((session_end - session_start).total_seconds()))
                    event_offsets = sorted(np.random.randint(5, total_seconds, size=event_count))

                    for seq, offset in enumerate(event_offsets, start=1):
                        ts = session_start + timedelta(seconds=int(offset))
                        if route == "/settings/billing":
                            pool = ["view_billing", "update_payment_method", "download_invoice", "open_subscription_settings"]
                            probs = [0.35, 0.20, 0.20, 0.25]
                        elif route == "/analytics/reports":
                            pool = ["view_dashboard", "run_report", "apply_filter", "click_export"]
                            probs = [0.25, 0.25, 0.30, 0.20]
                        elif route == "/projects/workspace":
                            pool = ["view_dashboard", "submit_form", "save_project", "open_detail_panel"]
                            probs = [0.20, 0.28, 0.24, 0.28]
                        else:
                            pool = ["view_dashboard", "open_widget", "submit_form", "navigate_section"]
                            probs = [0.35, 0.20, 0.20, 0.25]

                        event_name = np.random.choice(pool, p=probs)
                        if frustrated_user and api_wait > 3000 and np.random.rand() < 0.26:
                            event_name = "frequent_refresh"

                        click_rows.append(
                            {
                                "event_id": click_id,
                                "product_session_id": session_id,
                                "event_uuid": make_uuid(),
                                "event_name": event_name,
                                "event_category": "system_retry" if event_name == "frequent_refresh" else "user_action",
                                "page_screen_name": route.split('/')[-1].replace('-', '_').upper() or "HOME",
                                "ui_component_name": {
                                    "view_billing": "BILLING_PAGE",
                                    "update_payment_method": "PAYMENT_FORM",
                                    "download_invoice": "INVOICE_BUTTON",
                                    "open_subscription_settings": "PLAN_SETTINGS",
                                    "view_dashboard": "MAIN_DASHBOARD",
                                    "run_report": "RUN_REPORT_BUTTON",
                                    "apply_filter": "FILTER_PANEL",
                                    "click_export": "EXPORT_BUTTON",
                                    "submit_form": "SAVE_CTA",
                                    "save_project": "SAVE_BUTTON",
                                    "open_detail_panel": "DETAIL_PANEL",
                                    "open_widget": "WIDGET_CARD",
                                    "navigate_section": "NAV_BAR",
                                    "frequent_refresh": "BROWSER_RELOAD",
                                }[event_name],
                                "interaction_type": "keyboard_shortcut" if event_name == "frequent_refresh" else "click",
                                "event_timestamp": ts,
                                "ingestion_timestamp": ts + timedelta(milliseconds=int(np.random.randint(40, 300))),
                                "event_sequence_number": seq,
                                "latency_ms": int(np.clip(api_wait + np.random.randint(-120, 160), 10, 50000)),
                                "client_ip_address": login_rows[-1]["client_ip_address"],
                                "geo_country": master.country_code,
                                "geo_city": master.city,
                                "sdk_version": "web-sdk-v5.0.0" if device["platform_type"] == "WEB" else "mobile-sdk-v5.0.0",
                                "event_payload_json": json.dumps({"route": route, "component": device["device_model"]}),
                                "created_at": ts,
                            }
                        )
                        click_id += 1

        if acct.registration_source in ["IOS", "ANDROID"]:
            install_time = acct.created_at + timedelta(minutes=2)
            mobile_rows.append(
                {
                    "mobile_event_id": mobile_id,
                    "user_account_id": uid,
                    "application_event": "INSTALL",
                    "occurred_at": install_time,
                    "device_id": devices[0]["device_id"],
                    "app_version": "v3.5.0",
                    "os_version": devices[0]["operating_system"],
                    "push_token": f"tok_{uuid.uuid4().hex[:20]}",
                    "event_payload": json.dumps({"network_carrier": master.carrier_provider}),
                }
            )
            mobile_id += 1

            first_open = min(account_end, acct.created_at + timedelta(days=1))
            mobile_rows.append(
                {
                    "mobile_event_id": mobile_id,
                    "user_account_id": uid,
                    "application_event": "OPEN",
                    "occurred_at": first_open,
                    "device_id": devices[0]["device_id"],
                    "app_version": "v3.5.0",
                    "os_version": devices[0]["operating_system"],
                    "push_token": f"tok_{uuid.uuid4().hex[:20]}",
                    "event_payload": json.dumps({"network_carrier": master.carrier_provider}),
                }
            )
            mobile_id += 1

            if sub is not None and sub.subscription_status == "CANCELLED" and pd.notna(sub.subscription_ended_at) and np.random.rand() < 0.42:
                mobile_rows.append(
                    {
                        "mobile_event_id": mobile_id,
                        "user_account_id": uid,
                        "application_event": "UNINSTALL_SIGNAL",
                        "occurred_at": sub.subscription_ended_at + timedelta(hours=2),
                        "device_id": devices[0]["device_id"],
                        "app_version": "v3.5.0",
                        "os_version": devices[0]["operating_system"],
                        "push_token": f"tok_{uuid.uuid4().hex[:20]}",
                        "event_payload": json.dumps({"network_carrier": master.carrier_provider}),
                    }
                )
                mobile_id += 1

        for flag_key in ["pdf-generation-v2", "advanced-search-elastic"]:
            feature_rows.append(
                {
                    "exposure_id": feature_id,
                    "user_account_id": uid,
                    "feature_flag_key": flag_key,
                    "variant_key": np.random.choice(["treatment", "control"], p=[0.52, 0.48]),
                    "evaluation_reason": "RULE_MATCH",
                    "rule_set_version": "v1.1.0",
                    "exposure_context_json": json.dumps({"user_tier": "paid" if sub is not None else "free", "country_code": master.country_code}),
                    "exposed_at": acct.created_at + timedelta(hours=4 if flag_key == "pdf-generation-v2" else 5),
                }
            )
            feature_id += 1

        experiment_rows.append(
            {
                "assignment_id": experiment_id,
                "user_account_id": uid,
                "experiment_key": "EXP_CHECKOUT_FLOW_REDESIGN_2026",
                "treatment_group": np.random.choice(["VARIANT_A", "VARIANT_B", "CONTROL"], p=[0.34, 0.34, 0.32]),
                "assignment_hash": uuid.uuid4().hex[:16],
                "allocation_algorithm": "murmur3_salted_hash",
                "assigned_at": acct.created_at + timedelta(minutes=10),
            }
        )
        experiment_id += 1

        send_welcome = acct.created_at + timedelta(minutes=15)
        notifications.append(
            {
                "notification_event_id": notif_id,
                "user_account_id": uid,
                "notification_channel": "EMAIL",
                "template_id": "WELCOME_EMAIL",
                "provider_name": "SENDGRID",
                "provider_message_id": f"msg_{uuid.uuid4().hex[:14]}",
                "delivery_status": np.random.choice(["SENT", "OPENED", "FAILED"], p=[0.32, 0.63, 0.05]),
                "provider_response": json.dumps({"smtp_status_code": 250, "gateway_latency_ms": 110}),
                "created_at": send_welcome,
            }
        )
        notif_id += 1

        if sub is not None:
            notifications.append(
                {
                    "notification_event_id": notif_id,
                    "user_account_id": uid,
                    "notification_channel": "EMAIL",
                    "template_id": "TRIAL_ENDING_SOON",
                    "provider_name": "SENDGRID",
                    "provider_message_id": f"msg_{uuid.uuid4().hex[:14]}",
                    "delivery_status": np.random.choice(["SENT", "OPENED", "FAILED"], p=[0.36, 0.58, 0.06]),
                    "provider_response": json.dumps({"smtp_status_code": 250, "gateway_latency_ms": 120}),
                    "created_at": sub.trial_ends_at - timedelta(days=2),
                }
            )
            notif_id += 1

        if np.random.rand() < 0.22:
            if sub is not None and sub.subscription_status == "CANCELLED":
                category = "BILLING" if sub.cancellation_reason_code == "TOO_EXPENSIVE" else "UI_BUG" if sub.cancellation_reason_code == "POOR_PERFORMANCE" else "GENERAL_INQUIRY"
                created_ticket_at = sub.cancellation_requested_at if pd.notna(sub.cancellation_requested_at) else acct.created_at + timedelta(days=30)
            else:
                category = np.random.choice(["ACCOUNT", "GENERAL_INQUIRY", "BILLING", "UI_BUG"], p=[0.22, 0.34, 0.20, 0.24])
                created_ticket_at = acct.created_at + timedelta(days=int(np.random.randint(2, 220)))
                if created_ticket_at > account_end:
                    created_ticket_at = account_end - timedelta(hours=1)

            priority = "URGENT" if category == "UI_BUG" and frustrated_user else np.random.choice(["LOW", "MEDIUM", "HIGH"], p=[0.35, 0.45, 0.20])
            status = "OPEN" if frustrated_user and np.random.rand() < 0.45 else np.random.choice(["OPEN", "CLOSED"], p=[0.14, 0.86])
            first_response_at = created_ticket_at + timedelta(minutes=int(np.random.randint(15, 180)))
            resolved_at = pd.NaT if status == "OPEN" else first_response_at + timedelta(hours=int(np.random.randint(2, 72)))

            support_rows.append({
                "ticket_id": ticket_id,
                "user_account_id": uid,
                "external_ticket_id": f"zd_{uuid.uuid4().hex[:12]}",
                "ticket_status": status,
                "ticket_priority": priority,
                "category_code": category,
                "subcategory_code": "COMPONENT_CRASH" if category == "UI_BUG" else "PAYMENT_FAILURE" if category == "BILLING" else "GENERAL_ISSUE",
                "subject": "Payment failed processing" if category == "BILLING" else "System issue during workflow" if category == "UI_BUG" else "Need help with account usage",
                "description": "Generated from scenario-aware support logic.",
                "assigned_agent_id": int(np.random.randint(101, 125)),
                "first_response_at": first_response_at,
                "resolved_at": resolved_at,
                "created_at": created_ticket_at,
            })

            support_event_rows.append({
                "ticket_event_id": ticket_event_id,
                "ticket_id": ticket_id,
                "event_type": "INITIAL_ASSIGNMENT",
                "actor_type": "BOT",
                "actor_id": -99,
                "event_payload": json.dumps({"routing_tier": "L2_TECHNICAL_SUPPORT" if category == "UI_BUG" else "L1_SUPPORT"}),
                "created_at": created_ticket_at,
            })
            ticket_event_id += 1

            support_event_rows.append({
                "ticket_event_id": ticket_event_id,
                "ticket_id": ticket_id,
                "event_type": "AGENT_COMMENT",
                "actor_type": "AGENT",
                "actor_id": support_rows[-1]["assigned_agent_id"],
                "event_payload": json.dumps({"response_type": "initial_response"}),
                "created_at": first_response_at,
            })
            ticket_event_id += 1

            if status == "OPEN" or category in ["UI_BUG", "BILLING"] or np.random.rand() < 0.30:
                escalation_at = first_response_at + timedelta(hours=int(np.random.randint(1, 12)))
                support_event_rows.append({
                    "ticket_event_id": ticket_event_id,
                    "ticket_id": ticket_id,
                    "event_type": "ESCALATION",
                    "actor_type": "SYSTEM",
                    "actor_id": -2,
                    "event_payload": json.dumps({"escalation_reason": "SLA_BREACH" if status == "OPEN" else "CUSTOMER_REPORTED_ISSUE"}),
                    "created_at": escalation_at,
                })
                ticket_event_id += 1

            ticket_id += 1
        if np.random.rand() < 0.20:
            if sub is not None and sub.subscription_status == "CANCELLED":
                rating = np.random.choice([1, 2, 3, 4, 5], p=[0.20, 0.22, 0.24, 0.18, 0.16])
                submitted_at = sub.subscription_ended_at - timedelta(days=3) if pd.notna(sub.subscription_ended_at) else acct.created_at + timedelta(days=14)
            else:
                rating = np.random.choice([7, 8, 9, 10], p=[0.14, 0.30, 0.34, 0.22])
                submitted_at = acct.created_at + timedelta(days=14)

            if submitted_at > account_end:
                submitted_at = account_end - timedelta(hours=3)

            feedback_rows.append(
                {
                    "feedback_id": feedback_id,
                    "user_account_id": uid,
                    "feedback_type": "NPS",
                    "rating_value": int(rating),
                    "free_text_feedback": "Slow reports and page lag affected our daily workflow." if frustrated_user else "Great platform, helpful for day-to-day team operations.",
                    "source_screen": np.random.choice(["DASHBOARD_HOME", "SETTINGS_BILLING", "REPORTS_PAGE"]),
                    "session_id": make_uuid(),
                    "metadata_json": json.dumps({"sdk_environment": "PROD", "country_code": master.country_code}),
                    "submitted_at": submitted_at,
                }
            )
            feedback_id += 1

    if not subscription_accounts.empty:
        for sub in subscription_accounts.itertuples(index=False):
            master = master_lookup.loc[sub.user_account_id]
            cycle_days = 30 if sub.billing_cycle == "MONTHLY" else 365
            currency = master.currency_code
            tax_rate = master.tax_rate
            list_price = PLAN_CONFIG[sub.subscription_plan_code]["price"][currency]
            end_at = sub.subscription_ended_at if pd.notna(sub.subscription_ended_at) else CURRENT_DATE
            due_at = sub.subscription_started_at
            seq = 0

            while due_at <= end_at:
                invoice_status = "PAID"
                paid_at = due_at + timedelta(hours=int(np.random.randint(1, 24)))
                tx_status = "SUCCESS"
                failure_code = None
                failure_message = None
                response_code = "approved"

                if sub.subscription_status == "CANCELLED" and sub.cancellation_reason_code == "TOO_EXPENSIVE" and due_at >= end_at - timedelta(days=cycle_days):
                    invoice_status = "FAILED"
                    paid_at = pd.NaT
                    tx_status = "FAILED"
                    failure_code = "card_declined"
                    failure_message = "Insufficient funds during renewal attempt."
                    response_code = "insufficient_funds"
                    notifications.append(
                        {
                            "notification_event_id": notif_id,
                            "user_account_id": sub.user_account_id,
                            "notification_channel": "EMAIL",
                            "template_id": "DUNNING_NOTICE_FAIL",
                            "provider_name": "SENDGRID",
                            "provider_message_id": f"msg_{uuid.uuid4().hex[:14]}",
                            "delivery_status": np.random.choice(["SENT", "OPENED", "FAILED"], p=[0.40, 0.54, 0.06]),
                            "provider_response": json.dumps({"smtp_status_code": 250, "gateway_latency_ms": 145}),
                            "created_at": due_at + timedelta(hours=2),
                        }
                    )
                    notif_id += 1

                subtotal = float(list_price)
                discount = 0.0
                tax = round(subtotal * tax_rate, 2)
                total = round(subtotal - discount + tax, 2)

                invoice_rows.append(
                    {
                        "invoice_id": invoice_id,
                        "subscription_id": sub.subscription_id,
                        "external_invoice_id": f"inv_{uuid.uuid4().hex[:14]}",
                        "invoice_status": invoice_status,
                        "currency_code": currency,
                        "subtotal_amount": subtotal,
                        "tax_amount": tax,
                        "discount_amount": discount,
                        "total_amount": total,
                        "due_date": due_at,
                        "paid_at": paid_at,
                        "created_at": due_at - timedelta(days=1),
                    }
                )

                payment_rows.append(
                    {
                        "payment_transaction_id": payment_id,
                        "invoice_id": invoice_id,
                        "external_payment_id": f"ch_{uuid.uuid4().hex[:14]}",
                        "payment_provider": np.random.choice(["STRIPE", "ADYEN", "BRAINTREE"], p=[0.72, 0.18, 0.10]),
                        "payment_method_type": np.random.choice(["CARD", "ACH", "PAYPAL"], p=[0.80, 0.10, 0.10]),
                        "transaction_status": tx_status,
                        "failure_code": failure_code,
                        "failure_message": failure_message,
                        "processor_response_code": response_code,
                        "amount": total,
                        "currency_code": currency,
                        "provider_response_payload": json.dumps({"network_status": response_code}),
                        "initiated_at": due_at - timedelta(days=1),
                        "completed_at": paid_at,
                    }
                )

                invoice_id += 1
                payment_id += 1
                seq += 1
                due_at = sub.subscription_started_at + timedelta(days=cycle_days * seq)

    all_tables = {
        "app_user_accounts": pd.DataFrame(app_user_accounts),
        "app_user_profiles": pd.DataFrame(app_user_profiles),
        "user_master_profiles": pd.DataFrame(user_master),
        "user_device_profiles": pd.DataFrame(user_device_profiles),
        "subscription_accounts": pd.DataFrame(subscription_accounts),
        "subscription_state_history": pd.DataFrame(subscription_state_history),
        "auth_login_events": pd.DataFrame(login_rows),
        "auth_session_tokens": pd.DataFrame(session_rows),
        "billing_invoices": pd.DataFrame(invoice_rows),
        "payment_transactions": pd.DataFrame(payment_rows),
        "product_sessions": pd.DataFrame(product_session_rows),
        "clickstream_events": pd.DataFrame(click_rows),
        "frontend_performance_events": pd.DataFrame(perf_rows),
        "application_error_logs": pd.DataFrame(error_rows),
        "support_tickets": pd.DataFrame(support_rows),
        "support_ticket_events": pd.DataFrame(support_event_rows),
        "notification_delivery_events": pd.DataFrame(notifications),
        "mobile_application_events": pd.DataFrame(mobile_rows),
        "feature_flag_exposures": pd.DataFrame(feature_rows),
        "experiment_assignments": pd.DataFrame(experiment_rows),
        "user_feedback_submissions": pd.DataFrame(feedback_rows),
    }

    master_generation_config = {
        "identity_rules": {
            "country_drives": ["first_name", "last_name", "email_domain", "phone_number", "locale_code", "timezone_name", "currency_code", "city", "region"],
            "email_logic": "email local-part derived from normalized name with optional numeric suffix",
            "device_logic": "each user owns 1-3 stable devices; sessions reuse only those devices",
        },
        "behavior_rules": {
            "daily_usage": "activity generated per active day between account creation and account end",
            "session_bounds": "events and performance metrics always fall within session start/end",
            "geography": "login and event geography inherit user home country and city",
            "billing": "currency and tax depend on country; invoice cadence follows plan billing cycle",
        },
        "country_config": COUNTRY_CONFIG,
        "plan_config": PLAN_CONFIG,
    }

    with open(os.path.join(output_dir, "master_generation_config.json"), "w", encoding="utf-8") as f:
        json.dump(master_generation_config, f, indent=2, default=str)

    for name, df in all_tables.items():
        df.to_csv(os.path.join(output_dir, f"{name}.csv"), index=False)

    return all_tables


if __name__ == "__main__":
    tables = generate_data()
    print({name: df.shape for name, df in tables.items()})
