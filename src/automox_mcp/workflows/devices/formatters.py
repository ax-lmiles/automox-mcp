"""Formatters for device response data."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, cast

from .helpers import (
    DETAIL_KEY_MAP,
    POLICY_ASSIGNMENTS_LIMIT,
    POLICY_STATUS_LIMIT,
    SANITIZED_SEQUENCE_LIMIT,
    SANITIZED_STRING_LIMIT,
    SCRIPT_FIELDS,
    normalize_status,
    truncate_string,
)


def summarize_policy_status(
    entries: Any, *, limit: int = POLICY_STATUS_LIMIT
) -> tuple[list[dict[str, Any]], int]:
    """Condense Automox policy status records into a compact summary."""
    if not isinstance(entries, Sequence):
        return [], 0

    summary: list[dict[str, Any]] = []
    total = 0
    for item in entries:
        if not isinstance(item, Mapping):
            continue
        total += 1
        if len(summary) >= limit:
            continue
        result_text = item.get("result")
        if isinstance(result_text, str):
            result_text = result_text.strip()
            if result_text == "{}":
                result_text = None
        summary_item = {
            "policy_id": item.get("policy_id") or item.get("id"),
            "policy_name": item.get("policy_name") or item.get("name"),
            "status": normalize_status(
                item.get("status") or item.get("policy_status") or item.get("result_status")
            ),
            "execution_time": item.get("create_time") or item.get("updated_at"),
            "pending_count": item.get("pending_count"),
            "will_reboot": item.get("will_reboot"),
        }
        if result_text:
            summary_item["result"] = result_text
        summary.append({k: v for k, v in summary_item.items() if v not in (None, "", [], {})})

    return summary, total


def summarize_policy_assignments(
    entries: Any, *, limit: int = POLICY_ASSIGNMENTS_LIMIT
) -> tuple[list[dict[str, Any]], Counter[str], int]:
    """Summarize assigned Automox policies without embedding full scripts."""
    if not isinstance(entries, Sequence):
        return [], Counter(), 0

    summary: list[dict[str, Any]] = []
    status_counter: Counter[str] = Counter()
    total = 0

    for item in entries:
        if not isinstance(item, Mapping):
            continue
        total += 1
        status = normalize_status(item.get("status"))
        status_counter[status] += 1
        if len(summary) >= limit:
            continue

        configuration_raw = item.get("configuration")
        configuration: Mapping[str, Any] = (
            configuration_raw if isinstance(configuration_raw, Mapping) else {}
        )

        server_groups_raw = item.get("server_groups")
        group_names: list[str] = []
        group_remaining = 0
        server_group_count: int | None = None
        if isinstance(server_groups_raw, Sequence) and not isinstance(
            server_groups_raw, (str, bytes, bytearray)
        ):
            server_group_count = len(server_groups_raw)
            group_names = [
                str(group.get("name"))
                for group in server_groups_raw[:SANITIZED_SEQUENCE_LIMIT]
                if isinstance(group, Mapping) and group.get("name")
            ]
            group_remaining = max(len(server_groups_raw) - SANITIZED_SEQUENCE_LIMIT, 0)

        summary_item: dict[str, Any] = {
            "policy_id": item.get("id"),
            "policy_uuid": item.get("uuid") or item.get("policy_uuid"),
            "policy_name": item.get("name"),
            "policy_type": item.get("policy_type_name"),
            "status": status,
            "next_remediation": item.get("next_remediation"),
            "server_group_count": server_group_count,
            "server_groups": group_names if group_names else None,
            "auto_reboot": configuration.get("auto_reboot")
            if isinstance(configuration.get("auto_reboot"), bool)
            else configuration.get("auto_reboot"),
        }
        device_filters = configuration.get("device_filters")
        if isinstance(device_filters, Sequence) and not isinstance(
            device_filters, (str, bytes, bytearray)
        ):
            summary_item["device_filter_count"] = len(device_filters)
        if group_remaining:
            summary_item["server_groups_truncated"] = group_remaining

        summary.append({k: v for k, v in summary_item.items() if v not in (None, "", [], {})})

    return summary, status_counter, total


def extract_detail_facts(detail: Any) -> dict[str, Any] | None:
    """Pull notable inventory facts out of Automox device detail payloads."""
    if not isinstance(detail, Mapping):
        return None

    facts: dict[str, Any] = {}
    for raw_key, output_key in DETAIL_KEY_MAP.items():
        value = detail.get(raw_key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            preview = value[:SANITIZED_SEQUENCE_LIMIT]
            if len(value) > SANITIZED_SEQUENCE_LIMIT:
                preview = preview + [f"... {len(value) - SANITIZED_SEQUENCE_LIMIT} more"]
            facts[output_key] = preview
            continue
        if isinstance(value, Mapping):
            inner = {k.lower(): v for k, v in value.items() if v not in (None, "", [], {})}
            if inner:
                facts[output_key] = inner
            continue
        facts[output_key] = value

    return facts or None


def sanitize_raw_device_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Trim large strings and sequences so raw payloads stay within token budgets."""

    def sanitize(value: Any, depth: int = 0) -> Any:
        if depth > 8:
            return "... (max depth reached)"

        if isinstance(value, Mapping):
            sanitized: dict[str, Any] = {}
            for key, inner_value in value.items():
                if key in SCRIPT_FIELDS and isinstance(inner_value, str):
                    sanitized[key] = "... (script omitted to reduce payload size)"
                    continue
                sanitized[key] = sanitize(inner_value, depth + 1)
            return sanitized

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            trimmed = [sanitize(item, depth + 1) for item in value[:SANITIZED_SEQUENCE_LIMIT]]
            if len(value) > SANITIZED_SEQUENCE_LIMIT:
                trimmed.append(
                    {
                        "_note": (
                            f"{len(value) - SANITIZED_SEQUENCE_LIMIT} additional items truncated"
                        )
                    }
                )
            return trimmed

        if isinstance(value, str):
            return truncate_string(value, limit=SANITIZED_STRING_LIMIT)

        return value

    sanitized_payload = sanitize(dict(payload))
    return cast(dict[str, Any], sanitized_payload)
