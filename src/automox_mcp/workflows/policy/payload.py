"""Payload preparation for policy create/update operations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ...client import AutomoxClient
from .helpers import (
    deep_merge_dicts,
    ensure_list,
    normalize_filters,
    normalize_policy_type,
    normalize_schedule_days_input,
    normalize_schedule_time,
    sanitize_policy_payload,
)


def _apply_schedule_aliases(payload: dict[str, Any]) -> list[str]:
    """Normalize friendly schedule helpers into Automox bitmask fields."""
    warnings: list[str] = []
    schedule_block = payload.pop("schedule", None)
    if not isinstance(schedule_block, Mapping):
        return warnings

    schedule = dict(schedule_block)
    days_value = schedule.pop("days", schedule.pop("day", None))
    if days_value is not None:
        payload["schedule_days"] = normalize_schedule_days_input(days_value)

    time_value = schedule.pop("time", None)
    if time_value is not None:
        payload["schedule_time"] = normalize_schedule_time(time_value)

    timezone_value = schedule.pop("timezone", schedule.pop("tz", None))
    if timezone_value is not None and payload.get("scheduled_timezone") is None:
        payload["scheduled_timezone"] = str(timezone_value)
        payload.setdefault("use_scheduled_timezone", True)

    frequency = schedule.pop("frequency", None)
    if frequency:
        warnings.append(
            f"Ignored schedule.frequency='{frequency}'. Automox policies expect explicit "
            "bitmask fields (schedule_days/schedule_weeks_of_month/schedule_months)."
        )

    if schedule:
        warnings.append(
            "Ignored unrecognized keys in schedule block: " + ", ".join(sorted(schedule.keys()))
        )

    return warnings


def _normalize_device_filters(config: dict[str, Any]) -> None:
    """Normalize device_filters to proper Automox format."""
    filters = config.get("device_filters")
    if not filters:
        return
    if isinstance(filters, Mapping):
        return
    if not isinstance(filters, Sequence) or isinstance(filters, (str, bytes)):
        raise ValueError(
            "configuration.device_filters must be a list of filter definitions or device IDs."
        )

    filter_values: list[int] = []
    for item in filters:
        if isinstance(item, Mapping):
            return
        if isinstance(item, bool):
            raise ValueError(
                "configuration.device_filters cannot include boolean values. "
                "Provide Automox device IDs or full filter objects."
            )
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            integer_value = int(item)
            if integer_value <= 0:
                raise ValueError("Device filter IDs must be positive integers.")
            filter_values.append(integer_value)
            continue
        if isinstance(item, str):
            stripped = item.strip()
            if not stripped:
                continue
            if not stripped.isdigit():
                raise ValueError(f"Device filter value '{item}' is not a valid Automox device ID.")
            filter_values.append(int(stripped))
            continue
        raise ValueError(
            "configuration.device_filters must contain device IDs (ints/strings) "
            "or full filter definitions."
        )

    if not filter_values:
        return

    config["device_filters"] = [
        {
            "op": "in",
            "field": "device-id",
            "value": filter_values,
        }
    ]
    config["device_filters_enabled"] = True


def _validate_schedule_days(value: Any) -> int | None:
    """Validate schedule_days bitmask value."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("schedule_days must be an integer bitmask, not a boolean.")
    error_msg = (
        "schedule_days must be an integer bitmask aligned with Automox scheduling requirements."
    )
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if not text.isdigit():
            raise ValueError(error_msg)
        value = int(text)
    if not isinstance(value, int):
        raise ValueError(error_msg)
    if value < 0:
        raise ValueError("schedule_days must be non-negative.")
    return value


def _coerce_policy_payload_defaults(payload: dict[str, Any]) -> list[str]:
    """Apply Automox-friendly defaults and helper transformations."""
    warnings = _apply_schedule_aliases(payload)

    payload.setdefault("notes", "")
    payload.setdefault("server_groups", [])
    payload.setdefault("use_scheduled_timezone", False)
    payload.setdefault("schedule_weeks_of_month", 0)
    payload.setdefault("schedule_months", 0)

    config = payload.get("configuration")
    if not isinstance(config, Mapping):
        return warnings

    config_dict = dict(config)
    payload["configuration"] = config_dict

    policy_type = payload.get("policy_type_name")

    if policy_type == "patch":
        for field_name in ["auto_patch", "auto_reboot", "notify_user", "notify_reboot_user"]:
            if field_name in payload:
                field_value = payload.pop(field_name)
                if field_name not in config_dict:
                    config_dict[field_name] = field_value
                    warnings.append(
                        f"Moved '{field_name}' from top-level into configuration block "
                        f"for patch policy"
                    )

        for field_name in ["filter_name", "filter_names"]:
            if field_name in payload:
                field_value = payload.pop(field_name)
                if field_name not in config_dict:
                    config_dict[field_name] = field_value
                    warnings.append(
                        f"Moved '{field_name}' from top-level into configuration block "
                        f"for patch policy"
                    )

    if policy_type == "patch":
        has_filter_fields = bool(
            config_dict.get("filters")
            or config_dict.get("filter_name")
            or config_dict.get("filter_names")
        )
        patch_rule = config_dict.get("patch_rule")
        if not patch_rule:
            patch_rule = "filter" if has_filter_fields else "all"
            if has_filter_fields:
                warnings.append(
                    "Auto-set patch_rule='filter' because "
                    "filter_name/filter_names/filters was provided"
                )
        patch_rule = patch_rule.strip().lower()
        config_dict["patch_rule"] = patch_rule

        if patch_rule == "filter":
            available_filters = ensure_list(config_dict.get("filters"))
            available_filters.extend(ensure_list(config_dict.pop("filter_name", None)))
            available_filters.extend(ensure_list(config_dict.pop("filter_names", None)))
            normalized_filters = normalize_filters(available_filters)
            if not normalized_filters:
                raise ValueError(
                    "Patch policies using patch_rule='filter' require at least one "
                    "filter pattern. Provide configuration.filters (e.g., "
                    "['*Google Chrome*']) or filter_name/filter_names."
                )
            config_dict["filters"] = normalized_filters
            filter_type_value = config_dict.get("filter_type")
            config_dict["filter_type"] = (
                filter_type_value.strip().lower()
                if isinstance(filter_type_value, str) and filter_type_value.strip()
                else "include"
            )
        else:
            config_dict.pop("filter_name", None)
            config_dict.pop("filter_names", None)

        _normalize_device_filters(config_dict)
        if "device_filters_enabled" not in config_dict:
            config_dict["device_filters_enabled"] = bool(config_dict.get("device_filters"))
    else:
        _normalize_device_filters(config_dict)

    if not payload["use_scheduled_timezone"]:
        payload.pop("scheduled_timezone", None)

    validated_schedule_days = _validate_schedule_days(payload.get("schedule_days"))
    if validated_schedule_days is not None:
        payload["schedule_days"] = validated_schedule_days

    schedule_days_value = payload.get("schedule_days")
    has_schedule = isinstance(schedule_days_value, int) and schedule_days_value > 0

    if has_schedule:
        if payload.get("schedule_weeks_of_month", 0) == 0:
            payload["schedule_weeks_of_month"] = 62
            warnings.append(
                "Auto-set schedule_weeks_of_month=62 (all 5 weeks) because "
                "schedule_days was provided. Automox requires DAYS, WEEKS, and MONTHS "
                "to all be set for scheduled policies."
            )

        if payload.get("schedule_months", 0) == 0:
            payload["schedule_months"] = 8190
            warnings.append(
                "Auto-set schedule_months=8190 (all 12 months) because schedule_days was provided. "
                "Automox requires DAYS, WEEKS, and MONTHS to all be set for scheduled policies."
            )

    return warnings


def _ensure_required_policy_fields(
    payload: Mapping[str, Any],
    *,
    require_all: bool,
) -> None:
    """Validate required Automox fields are present before submission."""
    missing = []
    for field in (
        "name",
        "policy_type_name",
        "configuration",
        "schedule_days",
        "schedule_time",
        "use_scheduled_timezone",
        "server_groups",
        "notes",
    ):
        if payload.get(field) is None:
            missing.append(field)
    if missing and require_all:
        message = "Policy payload missing required fields: " + ", ".join(sorted(missing))
        hints: list[str] = []
        if "schedule_days" in missing or "schedule_time" in missing:
            hints.append(
                "Provide schedule_days (Automox bitmask) and schedule_time (HH:MM) "
                "or supply a 'schedule' helper block like "
                "{'schedule': {'days': ['monday', 'wednesday'], 'time': '02:00'}}."
            )
        if "configuration" in missing:
            hints.append(
                "Patch policies require a configuration object. For example: "
                "{'configuration': {'patch_rule': 'filter', 'filters': ['*Google Chrome*']}}."
            )
        if hints:
            message = f"{message}. Guidance: " + " ".join(hints)
        raise ValueError(message)
    configuration = payload.get("configuration")
    if configuration is not None and not isinstance(configuration, Mapping):
        raise ValueError("configuration must be an object matching Automox expectations.")
    server_groups = payload.get("server_groups")
    if server_groups is not None:
        if not isinstance(server_groups, Sequence) or isinstance(server_groups, (str, bytes)):
            raise ValueError("server_groups must be a list of Automox server group IDs.")


def prepare_policy_payload_for_create(
    policy_data: Mapping[str, Any],
    *,
    org_id: int,
) -> tuple[dict[str, Any], list[str]]:
    """Build the payload for creating a policy."""
    payload = sanitize_policy_payload(policy_data)
    payload["organization_id"] = org_id
    payload["policy_type_name"] = normalize_policy_type(payload.get("policy_type_name"))
    warnings = _coerce_policy_payload_defaults(payload)
    _ensure_required_policy_fields(payload, require_all=True)
    return payload, warnings


async def prepare_policy_payload_for_update(
    client: AutomoxClient,
    policy_id: int,
    policy_data: Mapping[str, Any],
    *,
    org_id: int,
    merge_existing: bool,
) -> tuple[dict[str, Any], Mapping[str, Any] | None, list[str]]:
    """Build the payload for updating a policy and return the latest Automox copy."""
    existing_original: Mapping[str, Any] | None = None
    existing_sanitized: Mapping[str, Any] | None = None
    if merge_existing:
        existing = await client.get(f"/policies/{policy_id}", params={"o": org_id}, api="console")
        if not isinstance(existing, Mapping):
            raise ValueError(f"Failed to retrieve policy {policy_id} for update.")
        existing_original = existing
        existing_sanitized = sanitize_policy_payload(existing)
        base = existing_sanitized
    else:
        base = {}
    overrides = sanitize_policy_payload(policy_data)
    if not overrides and not base:
        raise ValueError("No policy fields provided for update.")
    payload = deep_merge_dicts(base, overrides)

    if "policy_type_name" in payload and payload["policy_type_name"] is not None:
        payload["policy_type_name"] = normalize_policy_type(payload["policy_type_name"])
    elif existing_sanitized and existing_sanitized.get("policy_type_name"):
        payload["policy_type_name"] = normalize_policy_type(
            str(existing_sanitized.get("policy_type_name"))
        )
    else:
        raise ValueError(
            "policy_type_name is required when updating a policy without merge_existing."
        )

    if ("name" not in payload or payload["name"] is None) and existing_sanitized:
        payload["name"] = existing_sanitized.get("name")

    payload["organization_id"] = org_id
    if existing_sanitized:
        payload.setdefault("notes", existing_sanitized.get("notes"))
        payload.setdefault("server_groups", existing_sanitized.get("server_groups"))
        payload.setdefault(
            "schedule_weeks_of_month", existing_sanitized.get("schedule_weeks_of_month")
        )
        payload.setdefault("schedule_months", existing_sanitized.get("schedule_months"))
        payload.setdefault(
            "use_scheduled_timezone", existing_sanitized.get("use_scheduled_timezone")
        )
        if existing_sanitized.get("use_scheduled_timezone"):
            payload.setdefault("scheduled_timezone", existing_sanitized.get("scheduled_timezone"))

    warnings = _coerce_policy_payload_defaults(payload)
    payload["id"] = policy_id

    require_all = not merge_existing
    _ensure_required_policy_fields(payload, require_all=require_all)
    return payload, existing_original, warnings
