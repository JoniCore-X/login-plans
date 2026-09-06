from prometheus_client import Counter, Histogram

AUTH_LOGIN_ATTEMPTS = Counter(
    "auth_login_attempts_total",
    "Total login attempts",
    ["status"],
)

AUTH_REGISTER_ATTEMPTS = Counter(
    "auth_register_attempts_total",
    "Total registration attempts",
    ["status"],
)

AUTH_PASSWORD_CHANGES = Counter(
    "auth_password_changes_total",
    "Total password changes",
)

AUTH_SESSIONS_REVOKED = Counter(
    "auth_sessions_revoked_total",
    "Total sessions revoked",
    ["reason"],
)

AUTH_EMAIL_VERIFICATIONS = Counter(
    "auth_email_verifications_total",
    "Total email verifications",
    ["status"],
)

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Total rate limit hits",
    ["endpoint"],
)

PLANS_CREATED = Counter(
    "plans_created_total",
    "Total plans created",
)

PLANS_UPDATED = Counter(
    "plans_updated_total",
    "Total plans updated",
)

PLANS_ARCHIVED = Counter(
    "plans_archived_total",
    "Total plans archived",
)

PLANS_PUBLISHED = Counter(
    "plans_published_total",
    "Total plans published",
)

AUDIT_EVENTS = Counter(
    "audit_events_total",
    "Total audit events persisted",
    ["event_type"],
)

AUDIT_FAILURES = Counter(
    "audit_failures_total",
    "Total audit dispatch failures",
)

DB_OPERATION_DURATION = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration",
    ["operation", "table"],
)
