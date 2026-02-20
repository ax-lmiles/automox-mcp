"""Shared helpers and constants for policy workflows."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from fastmcp.exceptions import ToolError

# Constants
ALLOWED_POLICY_TYPES = {"patch", "custom", "required_software"}
READ_ONLY_POLICY_FIELDS = {
    "id",
    "uuid",
    "create_time",
    "server_count",
    "status",
    "next_remediation",
    "policy_uuid",
    "account_id",
}
OPERATION_CORE_KEYS = {"action", "policy", "policy_id", "merge_existing"}

DAY_NAME_TO_BITMASK = {
    "sunday": 128,
    "sun": 128,
    "monday": 2,
    "mon": 2,
    "tuesday": 4,
    "tue": 4,
    "tues": 4,
    "wednesday": 8,
    "wed": 8,
    "thursday": 16,
    "thu": 16,
    "thur": 16,
    "thurs": 16,
    "friday": 32,
    "fri": 32,
    "saturday": 64,
    "sat": 64,
}

DAY_INDEX_TO_NAME = {
    0: "sunday",
    1: "monday",
    2: "tuesday",
    3: "wednesday",
    4: "thursday",
    5: "friday",
    6: "saturday",
}

BITMASK_TO_DAY_NAME = {
    128: "sunday",
    2: "monday",
    4: "tuesday",
    8: "wednesday",
    16: "thursday",
    32: "friday",
    64: "saturday",
}

DAY_GROUP_ALIASES = {
    "weekday": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "weekdays": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "weekend": ["saturday", "sunday"],
    "weekends": ["saturday", "sunday"],
    "all": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    "everyday": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
}

SCHEDULE_TIME_PATTERN = re.compile(r"^(\d{1,2})(?::(\d{2}))?$")


def normalize_status(value: str | None) -> str:
    """Normalize policy/device status values to consistent format."""
    if not value:
        return "unknown"
    status = value.strip().lower()
    if status in {"success", "succeeded", "completed", "complete"}:
        return "success"
    if status in {"partial", "partial_success"}:
        return "partial"
    if "fail" in status or "error" in status:
        return "failed"
    if "cancel" in status:
        return "cancelled"
    return status


def take(sequence: Sequence[Any], limit: int) -> Sequence[Any]:
    """Take first N items from a sequence."""
    if limit <= 0:
        return []
    return sequence[:limit]


def ensure_list(value: Any) -> list[Any]:
    """Convert value to a list."""
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def normalize_filters(filters: Sequence[Any]) -> list[str]:
    """Normalize filter patterns with wildcards."""
    normalized: list[str] = []
    for item in filters:
        text = str(item).strip()
        if not text:
            continue
        if text.startswith("*") or text.endswith("*"):
            normalized.append(text)
        else:
            normalized.append(f"*{text}*")
    return normalized


def normalize_policy_type(value: str | None) -> str:
    """Normalize policy type names and validate the Automox enum."""
    if value is None:
        raise ValueError("policy_type_name is required for policy create/update operations.")
    normalized = value.strip().lower()
    if normalized not in ALLOWED_POLICY_TYPES:
        allowed = ", ".join(sorted(ALLOWED_POLICY_TYPES))
        raise ValueError(f"Unsupported policy_type_name '{value}'. Expected one of: {allowed}.")
    return normalized


def sanitize_policy_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Strip Automox response-only fields and deep copy mutable values."""
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if key in READ_ONLY_POLICY_FIELDS:
            continue
        sanitized[key] = deepcopy(value)
    return sanitized


def deep_merge_dicts(
    base: Mapping[str, Any],
    overrides: Mapping[str, Any],
) -> dict[str, Any]:
    """Recursively merge dictionaries, preferring override values."""
    merged = dict(base)
    for key, override_value in overrides.items():
        base_value = merged.get(key)
        if isinstance(base_value, Mapping) and isinstance(override_value, Mapping):
            merged[key] = deep_merge_dicts(base_value, override_value)
        else:
            merged[key] = deepcopy(override_value)
    return merged


def extract_policy_id_from_response(response: Any) -> int | None:
    """Attempt to pull a policy identifier from an Automox API response."""
    if not isinstance(response, Mapping):
        return None
    for candidate_key in ("id", "policy_id"):
        candidate = response.get(candidate_key)
        if isinstance(candidate, int):
            return candidate
        if isinstance(candidate, str):
            try:
                return int(candidate)
            except ValueError:
                continue
    return None


def decode_schedule_days_bitmask(bitmask: int) -> dict[str, Any]:
    """Decode a schedule_days bitmask into human-readable format."""
    if not bitmask or bitmask == 0:
        return {"interpretation": "Unscheduled (no days selected)"}

    days_map = {
        128: "Sunday",
        64: "Saturday",
        32: "Friday",
        16: "Thursday",
        8: "Wednesday",
        4: "Tuesday",
        2: "Monday",
    }

    selected_days = []
    for bit, day_name in days_map.items():
        if bitmask & bit:
            selected_days.append(day_name)

    interpretation = None
    if bitmask == 62:
        interpretation = "Weekdays (Monday through Friday)"
    elif bitmask == 192:
        interpretation = "Weekend (Saturday and Sunday)"
    elif bitmask == 254:
        interpretation = "Every day (all 7 days)"
    else:
        interpretation = f"{len(selected_days)} days: {', '.join(selected_days)}"

    return {
        "bitmask_value": bitmask,
        "interpretation": interpretation,
        "selected_days": selected_days,
        "reference": {
            "weekdays_Mon_to_Fri": 62,
            "weekend_Sat_and_Sun": 192,
            "every_day": 254,
            "note": (
                "Automox uses bit positions: 7=Sun(128), 6=Sat(64), 5=Fri(32), "
                "4=Thu(16), 3=Wed(8), 2=Tue(4), 1=Mon(2), 0=unused"
            ),
        },
    }


def normalize_schedule_time(value: Any) -> str | None:
    """Normalize schedule time to HH:MM format."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = SCHEDULE_TIME_PATTERN.fullmatch(text)
    if not match:
        raise ValueError(
            "schedule time must be provided in HH:MM (24-hour) format. Examples: '02:00', '18:30'."
        )
    hours = int(match.group(1))
    minutes = int(match.group(2) or "0")
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError("schedule time must use a valid 24-hour clock (00:00 through 23:59).")
    return f"{hours:02d}:{minutes:02d}"


def expand_day_alias(value: str) -> list[str]:
    """Expand day alias to list of day names."""
    alias = value.lower()
    if alias in DAY_GROUP_ALIASES:
        return DAY_GROUP_ALIASES[alias]
    if alias in DAY_NAME_TO_BITMASK:
        bitmask = DAY_NAME_TO_BITMASK[alias]
        day_name = BITMASK_TO_DAY_NAME.get(bitmask)
        if day_name:
            return [day_name]
    raise ValueError(
        f"Unrecognized day name '{value}'. Use values like 'monday', 'wed', "
        "'weekdays', or provide numeric day indexes (0-6 or 1-7)."
    )


def normalize_schedule_days_input(value: Any) -> int | None:
    """Normalize schedule days input to bitmask."""
    if value is None:
        return None
    items = ensure_list(value)
    if not items:
        return None

    bitmask = 0
    for item in items:
        if isinstance(item, Mapping):
            raise ValueError(
                "schedule.days must be a list of names or integers, not nested objects."
            )
        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            if text.isdigit():
                item = int(text)
            else:
                for expanded in expand_day_alias(text):
                    normalized_bit = DAY_NAME_TO_BITMASK[expanded]
                    bitmask |= normalized_bit
                continue
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            integer_value = int(item)
            if integer_value not in range(0, 7) and integer_value not in range(1, 8):
                raise ValueError(
                    "Numeric schedule days must be in the range 0-6 (Sunday-Saturday) "
                    "or 1-7 (Monday-Sunday)."
                )
            if integer_value in range(1, 8):
                index = integer_value % 7
            else:
                index = integer_value
            day_name = DAY_INDEX_TO_NAME[index]
            bitmask |= DAY_NAME_TO_BITMASK[day_name]
            continue
        raise ValueError(
            "schedule.days must contain day names (e.g., 'monday') or numeric day indexes."
        )

    return bitmask or None


def normalize_policy_operations_input(raw_operations: Sequence[Any]) -> list[dict[str, Any]]:
    """Normalize loosely structured operations into the expected payload shape."""
    normalized: list[dict[str, Any]] = []
    for index, raw_op in enumerate(raw_operations):
        if not isinstance(raw_op, Mapping):
            raise ValueError(
                f"Operation at index {index} must be an object. "
                f"Example: {{'action': 'create', 'policy': {{'name': '...', ...}}}}"
            )

        op_dict = dict(raw_op)

        if "operation" in op_dict and "action" not in op_dict:
            operation_value = op_dict.pop("operation")
            raise ToolError(
                f"Operation at index {index} uses 'operation' field but should use "
                f"'action' field instead. "
                f"Found: 'operation': '{operation_value}'. "
                f"Change to: 'action': '{operation_value}'. "
                f"\n\nCorrect format:\n"
                f"{{\n"
                f'  "action": "{operation_value}",\n'
                f'  "policy": {{\n'
                f'    "name": "Policy Name",\n'
                f'    "policy_type_name": "patch",\n'
                f'    "configuration": {{ ... }},\n'
                f'    "schedule": {{ "days": ["monday"], "time": "02:00" }}\n'
                f"  }}\n"
                f"}}"
            )

        if "action" not in op_dict:
            raise ToolError(
                f"Operation at index {index} is missing required 'action' field. "
                f"Must be either 'create' or 'update'. "
                f"\n\nExample for create:\n"
                f"{{\n"
                f'  "action": "create",\n'
                f'  "policy": {{ ... }}\n'
                f"}}\n\n"
                f"Example for update:\n"
                f"{{\n"
                f'  "action": "update",\n'
                f'  "policy_id": 12345,\n'
                f'  "policy": {{ ... }}\n'
                f"}}"
            )

        policy_payload = op_dict.get("policy")
        if not isinstance(policy_payload, Mapping):
            policy_payload = {
                key: value
                for key, value in list(op_dict.items())
                if key not in OPERATION_CORE_KEYS
            }
            for key in list(policy_payload.keys()):
                op_dict.pop(key, None)
            op_dict["policy"] = policy_payload
        else:
            op_dict["policy"] = dict(policy_payload)

        policy = op_dict["policy"]

        if "policy_type" in policy and "policy_type_name" not in policy:
            policy["policy_type_name"] = policy.pop("policy_type")
        if "policyType" in policy and "policy_type_name" not in policy:
            policy["policy_type_name"] = policy.pop("policyType")

        if "configuration" in policy and isinstance(policy["configuration"], Mapping):
            config = dict(policy["configuration"])
            if "software_name" in config and "filters" not in config:
                config["filters"] = [f"*{config.pop('software_name')}*"]
            if "filter_type" in config:
                config.pop("filter_type")
            policy["configuration"] = config

        if "device_filters" in policy and isinstance(policy["device_filters"], list):
            filters = policy["device_filters"]
            if filters and isinstance(filters[0], Mapping) and "device_id" in filters[0]:
                device_ids = [f["device_id"] for f in filters if "device_id" in f]
                policy.pop("device_filters")
                if "notes" not in policy:
                    policy["notes"] = ""
                policy["notes"] += f" Target device IDs: {device_ids}"

        if policy.get("policy_type_name") == "patch" and "configuration" not in policy:
            raise ToolError(
                f"Operation at index {index}: Patch policies require a 'configuration' block. "
                f"Example: {{'configuration': {{'patch_rule': 'filter', "
                f"'filters': ['*Google Chrome*']}}}}"
            )

        normalized.append(op_dict)

    return normalized
