"""Device health aggregation workflows."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from ...client import AutomoxClient
from .helpers import (
    DEFAULT_MAX_STALE_DEVICES,
    MAX_HEALTH_RESPONSE_BYTES,
    MAX_STALE_DEVICE_LIMIT,
    STALE_CHECK_IN_THRESHOLD_DAYS,
    add_followup,
    calculate_days_since_check_in,
    format_device_display_name,
    summarize_device_common_fields,
)


async def summarize_device_health(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    group_id: int | None = None,
    include_unmanaged: bool = False,
    limit: int | None = 500,
    max_stale_devices: int | None = DEFAULT_MAX_STALE_DEVICES,
    current_time: datetime | None = None,
) -> dict[str, Any]:
    """Aggregate high-level health signals for devices in the organization."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    effective_limit = 500
    if limit is not None:
        effective_limit = max(1, min(limit, 500))

    params = {"o": resolved_org_id, "limit": effective_limit}
    if group_id is not None:
        params["groupId"] = group_id

    devices = await client.get("/servers", params=params, api="console")
    devices = devices if isinstance(devices, Sequence) else []

    totals: Counter[str] = Counter()
    device_status_counts: Counter[str] = Counter()
    policy_execution_counts: Counter[str] = Counter()
    platform_counts: Counter[str] = Counter()
    compliant_counts: Counter[str] = Counter()
    devices_with_pending_patches = 0
    devices_needing_attention = 0
    check_in_recency_counts: Counter[str] = Counter()
    stale_devices: list[dict[str, Any]] = []

    stale_limit: int | None
    if max_stale_devices is None:
        stale_limit = None
    else:
        normalized_limit = max(0, min(int(max_stale_devices), MAX_STALE_DEVICE_LIMIT))
        stale_limit = normalized_limit

    for device in devices:
        summary_fields = summarize_device_common_fields(device)
        is_managed = summary_fields["is_managed"]
        totals["managed" if is_managed else "unmanaged"] += 1
        if not include_unmanaged and not is_managed:
            continue

        device_status_counts[summary_fields["device_status"]] += 1
        policy_execution_counts[summary_fields["policy_status"]] += 1
        platform = summary_fields["platform"] or "unknown"
        platform_counts[platform] += 1

        device_compliant = device.get("compliant")
        device_pending = device.get("pending")
        if device_compliant is True and device_pending is False:
            compliant_counts["compliant"] += 1
        elif device_compliant is False or device_pending is True:
            compliant_counts["non_compliant"] += 1
        else:
            compliant_counts["unknown"] += 1

        pending_patches = summary_fields.get("pending_patches")
        if isinstance(pending_patches, (int, float)) and pending_patches > 0:
            devices_with_pending_patches += 1

        if summary_fields.get("needs_attention"):
            devices_needing_attention += 1

        last_check_in = summary_fields["last_check_in"]
        days_since = calculate_days_since_check_in(last_check_in, now=current_time)

        if days_since is None:
            check_in_recency_counts["never_connected"] += 1
        elif days_since == 0:
            check_in_recency_counts["last_24_hours"] += 1
        elif days_since <= 7:
            check_in_recency_counts["last_7_days"] += 1
        elif days_since <= 30:
            check_in_recency_counts["last_30_days"] += 1
        else:
            check_in_recency_counts["30_plus_days"] += 1

        stale_reason = None
        if last_check_in is None:
            stale_reason = "no check-in recorded"
        elif days_since is None:
            stale_reason = "invalid check-in timestamp"
        elif days_since > STALE_CHECK_IN_THRESHOLD_DAYS:
            stale_reason = (
                f"last check-in {days_since} days ago "
                f"(>{STALE_CHECK_IN_THRESHOLD_DAYS} day threshold)"
            )

        if stale_reason:
            stale_devices.append(
                {
                    "device_id": device.get("id"),
                    "display_name": format_device_display_name(device) or device.get("name"),
                    "platform": platform,
                    "policy_status": summary_fields["policy_status"],
                    "last_check_in": last_check_in,
                    "days_since_check_in": days_since,
                    "needs_attention": summary_fields.get("needs_attention"),
                    "reason": stale_reason,
                }
            )

    total_devices = sum(totals.values()) if include_unmanaged else totals["managed"]
    if stale_limit is None:
        stale_preview = list(stale_devices)
    else:
        stale_preview = stale_devices[:stale_limit]

    data = {
        "total_devices": total_devices,
        "managed_breakdown": dict(totals),
        "device_status_breakdown": dict(device_status_counts),
        "policy_execution_breakdown": dict(policy_execution_counts),
        "platform_breakdown": dict(platform_counts),
        "compliant_devices": compliant_counts["compliant"],
        "devices_with_pending_patches": devices_with_pending_patches,
        "devices_needing_attention": devices_needing_attention,
        "check_in_recency_breakdown": dict(check_in_recency_counts),
        "stale_devices": stale_preview,
    }

    metadata = {}
    metadata.update(
        {
            "deprecated_endpoint": False,
            "org_id": resolved_org_id,
            "group_id": group_id,
            "include_unmanaged": include_unmanaged,
            "requested_limit": limit,
            "effective_limit": effective_limit,
            "fetched_device_count": len(devices),
            "max_stale_devices": stale_limit,
            "stale_device_count": len(stale_devices),
            "stale_check_in_threshold_days": STALE_CHECK_IN_THRESHOLD_DAYS,
        }
    )
    if stale_limit is not None and len(stale_devices) > stale_limit:
        metadata["stale_devices_truncated"] = True

    response = {"data": data, "metadata": metadata}
    try:
        response_size = len(json.dumps(response))
    except (TypeError, ValueError):
        response_size = None

    if response_size and response_size > MAX_HEALTH_RESPONSE_BYTES:
        metadata["response_truncated"] = True
        add_followup(
            metadata,
            "device_health_summary",
            "Reduce the limit or group by server group to shrink the response.",
        )
        add_followup(
            metadata,
            "search_devices",
            "Filter by hostname, tag, or pending patches to focus on specific devices.",
        )
        response = {"data": data, "metadata": metadata}
        try:
            response_size = len(json.dumps(response))
        except (TypeError, ValueError):
            response_size = None

    if response_size is not None:
        metadata["approx_response_bytes"] = response_size

    return response
