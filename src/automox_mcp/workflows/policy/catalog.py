"""Policy catalog and detail workflows."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from ...client import AutomoxAPIError, AutomoxClient
from ...utils import resolve_org_uuid
from .execution import summarize_policy_execution_history
from .helpers import decode_schedule_days_bitmask, normalize_status

logger = logging.getLogger(__name__)


async def summarize_policies(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    limit: int = 20,
    page: int | None = 0,
    include_inactive: bool = False,
) -> dict[str, Any]:
    """Provide a curated view of Automox policies."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params = {"o": resolved_org_id}
    if limit is not None:
        params["limit"] = limit
    if page is not None:
        params["page"] = page

    policies: list[Mapping[str, Any]] = []
    current_page = page or 0
    type_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    filtered: list[Mapping[str, Any]] = []
    preview: list[Mapping[str, Any]] = []

    while True:
        policies_response = await client.get("/policies", params=params, api="console")
        page_results: list[Mapping[str, Any]] = []
        if isinstance(policies_response, Sequence):
            page_results = [item for item in policies_response if isinstance(item, Mapping)]

        policies.extend(page_results)

        for policy_item in page_results:
            if not isinstance(policy_item, Mapping):
                continue
            active_flag = (
                policy_item.get("active")
                or policy_item.get("enabled")
                or policy_item.get("is_active")
            )
            is_active = False if active_flag in (False, 0, "false", "inactive") else True
            if not include_inactive and not is_active:
                continue

            policy_type = (
                policy_item.get("policy_type") or policy_item.get("type") or "unknown"
            ).lower()
            type_counts[policy_type] += 1
            status = normalize_status(
                policy_item.get("status") or ("active" if is_active else "inactive")
            )
            status_counts[status] += 1

            filtered.append(policy_item)

            if limit is None or len(preview) < limit:
                preview.append(
                    {
                        "policy_id": policy_item.get("id"),
                        "policy_uuid": policy_item.get("guid") or policy_item.get("uuid"),
                        "name": policy_item.get("name"),
                        "type": policy_item.get("policy_type") or policy_item.get("type"),
                        "status": policy_item.get("status"),
                        "targets": policy_item.get("target"),
                        "next_run": policy_item.get("next_run"),
                    }
                )

        if limit is None:
            break

        has_reached_preview_cap = len(preview) >= limit
        next_page_index = current_page + 1
        params["page"] = next_page_index
        current_page = next_page_index

        if has_reached_preview_cap or not page_results:
            break

    stats_params = {"o": resolved_org_id}
    stats_data = await client.get("/policystats", params=stats_params, api="console")
    total_available: int | None = None
    if isinstance(stats_data, Sequence):
        policy_ids = {
            item.get("policy_id")
            for item in stats_data
            if isinstance(item, Mapping) and item.get("policy_id") is not None
        }
        if policy_ids:
            total_available = len(policy_ids)
        else:
            total_available = len([item for item in stats_data if isinstance(item, Mapping)])

    returned_count_raw = len(policies)
    returned_count = len(preview)
    normalized_page = page if page is None else max(page, 0)
    if total_available is not None and limit is not None and normalized_page is not None:
        has_more = (normalized_page + 1) * limit < total_available
    else:
        has_more = bool(limit is not None and returned_count_raw >= limit)
    next_page: int | None = None
    if has_more and normalized_page is not None:
        next_page = normalized_page + 1
    previous_page: int | None = None
    if normalized_page is not None and normalized_page > 0:
        previous_page = normalized_page - 1

    pagination: dict[str, Any] = {
        "page": normalized_page,
        "current_page": normalized_page,
        "limit": limit,
        "returned_count": returned_count,
        "returned_count_raw": returned_count_raw,
        "has_more": bool(has_more),
        "next_page": next_page,
        "previous_page": previous_page,
    }
    if total_available is not None:
        pagination["total_count"] = total_available
    pagination["filtered_count"] = len(filtered)

    suggested_next_call: dict[str, Any] | None = None
    if has_more and normalized_page is not None:
        suggested_next_call = {
            "tool": "policy_catalog",
            "args": {
                "page": normalized_page + 1,
                "limit": limit,
                "include_inactive": include_inactive,
            },
        }

    data = {
        "total_policies_considered": len(filtered),
        "policies_returned": len(preview),
        "policy_type_breakdown": dict(type_counts),
        "status_breakdown": dict(status_counts),
        "policies": preview,
        "policy_stats": stats_data,
    }
    if total_available is not None:
        data["total_policies_available"] = total_available

    metadata: dict[str, Any] = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "requested_limit": limit,
        "requested_page": normalized_page,
        "include_inactive": include_inactive,
        "current_page": normalized_page,
        "limit": limit,
        "pagination": pagination,
    }
    if total_available is not None:
        metadata["total_policies_available"] = total_available
    if suggested_next_call:
        metadata["suggested_next_call"] = suggested_next_call
    if has_more:
        note = (
            f"{returned_count} of {total_available} policies returned; follow "
            f"metadata.suggested_next_call or increment page to continue pagination."
            if total_available is not None
            else "Partial results returned; follow metadata.suggested_next_call or "
            "increment page to continue pagination."
        )
        metadata["notes"] = [note]

    return {
        "data": data,
        "metadata": metadata,
    }


async def describe_policy(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    policy_id: int,
    include_recent_runs: int = 5,
) -> dict[str, Any]:
    """Return the configuration and recent history for a specific policy."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params = {"o": resolved_org_id}
    try:
        policy_response = await client.get(f"/policies/{policy_id}", params=params, api="console")
    except Exception as e:
        raise ValueError(
            f"Failed to retrieve policy {policy_id} from organization {resolved_org_id}. "
            f"Request: GET /policies/{policy_id}?o={resolved_org_id}. "
            f"The policy may not exist in this organization, may have been deleted, "
            f"or may belong to a different org/zone. Use policy_catalog to verify. "
            f"Error: {e}"
        ) from e

    policy_data = policy_response if isinstance(policy_response, Mapping) else {}
    policy_uuid_value = (
        policy_data.get("guid") or policy_data.get("uuid") or policy_data.get("policy_uuid")
    )

    recent_activity = None
    if include_recent_runs and policy_uuid_value:
        history_org_uuid: UUID | None = None
        raw_policy_org_uuid = (
            policy_data.get("org_uuid")
            or policy_data.get("organization_uuid")
            or policy_data.get("organization_uid")
        )
        if raw_policy_org_uuid:
            try:
                history_org_uuid = UUID(str(raw_policy_org_uuid))
            except (TypeError, ValueError):
                history_org_uuid = None
        if history_org_uuid is None:
            try:
                resolved_org_uuid = await resolve_org_uuid(
                    client,
                    org_id=resolved_org_id,
                    allow_account_uuid=False,
                )
            except ValueError:
                resolved_org_uuid = None
            if resolved_org_uuid:
                try:
                    history_org_uuid = UUID(resolved_org_uuid)
                except (TypeError, ValueError):
                    history_org_uuid = None

        if history_org_uuid is not None:
            try:
                policy_uuid = UUID(str(policy_uuid_value))
                history = await summarize_policy_execution_history(
                    client,
                    org_uuid=history_org_uuid,
                    policy_uuid=policy_uuid,
                    report_days=30,
                    limit=include_recent_runs,
                )
                recent_activity = {
                    "status_breakdown": history["data"].get("status_breakdown"),
                    "recent_executions": history["data"].get("recent_executions"),
                }
            except (AutomoxAPIError, ValueError, TypeError, KeyError) as exc:
                logger.debug("Failed to fetch policy history: %s", exc)
                recent_activity = None

    schedule_interpretation = None
    schedule_days = policy_data.get("schedule_days")
    if schedule_days is not None:
        schedule_interpretation = decode_schedule_days_bitmask(schedule_days)

    data = {
        "policy": policy_data,
        "recent_activity": recent_activity,
    }

    if schedule_interpretation:
        data["schedule_interpretation"] = schedule_interpretation
        data["_important"] = {
            "current_schedule": schedule_interpretation["interpretation"],
            "schedule_days_bitmask": schedule_days,
            "schedule_time": policy_data.get("schedule_time"),
            "note": (
                "Use resource://policies/schedule-syntax for scheduling help. "
                "To update schedule, use {'days': ['weekend'], 'time': '02:00'} syntax."
            ),
        }

    metadata: dict[str, Any] = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "policy_id": policy_id,
        "include_recent_runs": include_recent_runs,
    }
    if policy_uuid_value:
        metadata["policy_uuid"] = str(policy_uuid_value)

    return {
        "data": data,
        "metadata": metadata,
    }
