"""Shared helpers and constants for device workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

# Constants
POLICY_STATUS_LIMIT = 12
POLICY_ASSIGNMENTS_LIMIT = 10
SANITIZED_SEQUENCE_LIMIT = 5
SANITIZED_STRING_LIMIT = 400
SCRIPT_FIELDS = {
    "evaluation_code",
    "remediation_code",
    "installation_code",
    "script",
    "powershell_script",
    "powershellScript",
}
DETAIL_KEY_MAP = {
    "MODEL": "model",
    "OS": "os_name",
    "OS_VERSION": "os_version",
    "SERIAL_NUMBER": "serial_number",
    "CHASSIS_TYPE": "chassis_type",
    "LAST_REBOOT_TIME": "last_reboot",
    "LAST_USER_LOGON": "last_user_logon",
    "IPS": "ip_addresses",
    "CPU": "cpu",
    "MEMORY": "memory",
    "DISK_TOTAL": "disk_total",
    "DISK_USED": "disk_used",
}

MAX_HEALTH_RESPONSE_BYTES = 18_000
DEFAULT_MAX_STALE_DEVICES = 25
MAX_STALE_DEVICE_LIMIT = 200
STALE_CHECK_IN_THRESHOLD_DAYS = 30


def normalize_status(value: Any) -> str:
    """Normalize policy/device status values to consistent format."""
    if value in (None, "", [], {}):
        return "unknown"

    if isinstance(value, Mapping):
        for key in ("status", "policy_status", "result_status", "state"):
            inner = value.get(key)
            if inner not in (None, "", [], {}):
                return normalize_status(inner)
        return "unknown"

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        statuses: list[str] = []
        for item in value:
            normalized = normalize_status(item)
            if normalized != "unknown":
                statuses.append(normalized)
        if not statuses:
            return "unknown"
        unique_statuses = set(statuses)
        if len(unique_statuses) == 1:
            return next(iter(unique_statuses))
        return "mixed"

    status = str(value).strip().lower()
    if not status:
        return "unknown"
    if any(ch in status for ch in "{}[]"):
        return "mixed"
    if status in {"success", "succeeded", "completed", "complete"}:
        return "success"
    if status in {"partial", "partial_success"}:
        return "partial"
    if "fail" in status or "error" in status:
        return "failed"
    if "cancel" in status:
        return "cancelled"
    return status


def extract_last_check_in(device: Mapping[str, Any]) -> str | None:
    """Find the most relevant last check-in timestamp for a device."""
    for key in (
        "last_check_in",
        "last_seen",
        "last_seen_time",
        "last_refresh_time",
        "last_process_time",
        "last_update_time",
        "last_disconnect_time",
    ):
        value = device.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def calculate_days_since_check_in(
    timestamp_str: str | None, *, now: datetime | None = None
) -> int | None:
    """Calculate the number of days since a check-in timestamp."""
    if not timestamp_str:
        return None

    try:
        check_in_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        reference_time = now or datetime.now(UTC)
        delta = reference_time - check_in_time
        return int(delta.total_seconds() / 86400)
    except (ValueError, AttributeError):
        return None


def format_device_display_name(device: Mapping[str, Any]) -> str | None:
    """Format device display name with custom name in parentheses if present."""
    hostname_value = device.get("name") or device.get("hostname") or device.get("device_name")
    hostname: str | None
    if isinstance(hostname_value, str):
        hostname = hostname_value.strip() or None
    elif hostname_value is not None:
        hostname = str(hostname_value).strip() or None
    else:
        hostname = None
    if not hostname:
        return None

    custom_name_value = device.get("custom_name")
    custom_name: str | None
    if isinstance(custom_name_value, str):
        custom_name = custom_name_value.strip() or None
    elif custom_name_value is not None:
        custom_name = str(custom_name_value).strip() or None
    else:
        custom_name = None

    if custom_name:
        return f"{hostname} ({custom_name})"
    return hostname


def extract_policy_status(device: Mapping[str, Any]) -> str:
    """Derive the overall policy status string reported by Automox."""
    status_mapping = device.get("status")
    if isinstance(status_mapping, Mapping):
        primary = (
            status_mapping.get("policy_status")
            or status_mapping.get("device_status")
            or status_mapping.get("agent_status")
        )
        normalized = normalize_status(primary)
        if normalized != "unknown":
            return normalized

    direct = device.get("policy_status")
    if isinstance(direct, str):
        return normalize_status(direct)

    return "unknown"


def count_failed_policies(device: Mapping[str, Any]) -> int:
    """Count the number of policy entries marked non-compliant."""
    status_mapping = device.get("status")
    entries = None
    if isinstance(status_mapping, Mapping):
        entries = status_mapping.get("policy_statuses")
    if not isinstance(entries, Sequence):
        return 0
    failures = 0
    for entry in entries:
        if isinstance(entry, Mapping) and entry.get("compliant") is False:
            failures += 1
    return failures


def summarize_device_common_fields(device: Mapping[str, Any]) -> dict[str, Any]:
    """Extract shared classification fields used by inventory/health summaries."""
    managed_flag = device.get("managed")
    is_managed = bool(managed_flag) if managed_flag is not None else True

    policy_status = extract_policy_status(device)
    last_check_in = extract_last_check_in(device)

    pending_patches = device.get("pending_patches")
    if not isinstance(pending_patches, (int, float)):
        pending_patches = None

    has_pending_updates = device.get("pending")
    if not isinstance(has_pending_updates, bool):
        has_pending_updates = None

    needs_attention = device.get("needs_attention")
    if not isinstance(needs_attention, bool):
        needs_attention = None

    status_mapping = device.get("status")
    device_status_value = None
    if isinstance(status_mapping, Mapping):
        device_status_value = status_mapping.get("device_status") or status_mapping.get("status")
    device_status = normalize_status(device_status_value)

    platform_raw = device.get("os_name") or device.get("platform") or "unknown"
    platform = str(platform_raw).lower()

    return {
        "is_managed": is_managed,
        "policy_status": policy_status,
        "pending_patches": pending_patches,
        "has_pending_updates": has_pending_updates,
        "needs_attention": needs_attention,
        "last_check_in": last_check_in,
        "device_status": device_status,
        "platform": platform,
    }


def add_followup(metadata: dict[str, Any], tool: str, note: str) -> None:
    """Append a suggested follow-up entry without introducing duplicates."""
    followups = metadata.setdefault("suggested_followups", [])
    entry = {"tool": tool, "note": note}
    if entry not in followups:
        followups.append(entry)


def truncate_string(value: str, *, limit: int = SANITIZED_STRING_LIMIT) -> str:
    """Return a truncated string with a note when long values are trimmed."""
    if len(value) <= limit:
        return value
    trimmed = value[:limit]
    remaining = len(value) - limit
    return f"{trimmed}... ({remaining} chars truncated)"
