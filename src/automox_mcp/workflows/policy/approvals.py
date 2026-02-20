"""Patch approval workflows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from ...client import AutomoxClient


async def summarize_patch_approvals(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    status: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Summarize pending Automox patch approvals and provide decision context."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params = {"o": resolved_org_id, "limit": limit}
    approvals = await client.get("/approvals", params=params, api="console")
    approvals = approvals if isinstance(approvals, Sequence) else []

    status_filter = (status or "").lower()
    status_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    pending_items = []

    for approval_item in approvals:
        if not isinstance(approval_item, Mapping):
            continue
        approval_status = (approval_item.get("status") or "unknown").lower()
        status_counts[approval_status] += 1

        if status_filter and approval_status != status_filter:
            continue

        severity = (
            approval_item.get("severity") or approval_item.get("cvss_severity") or "unknown"
        ).lower()
        severity_counts[severity] += 1

        pending_items.append(
            {
                "approval_id": approval_item.get("id"),
                "title": approval_item.get("title") or approval_item.get("name"),
                "status": approval_item.get("status"),
                "severity": approval_item.get("severity"),
                "device_count": approval_item.get("device_count")
                or approval_item.get("devices_affected"),
                "created_at": approval_item.get("created_at"),
                "deadline": approval_item.get("deadline") or approval_item.get("expires_at"),
            }
        )

    data = {
        "total_approvals_considered": len(approvals),
        "status_breakdown": dict(status_counts),
        "severity_breakdown": dict(severity_counts),
        "approvals": pending_items[:limit],
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "status_filter": status_filter or None,
        "requested_limit": limit,
    }

    return {
        "data": data,
        "metadata": metadata,
    }


async def resolve_patch_approval(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    approval_id: int,
    decision: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Approve or reject an Automox patch approval request."""
    decision_normalized = decision.lower()
    decision_map = {
        "approve": "approved",
        "approved": "approved",
        "accept": "approved",
        "deny": "rejected",
        "reject": "rejected",
        "rejected": "rejected",
    }
    status_value = decision_map.get(decision_normalized)
    if not status_value:
        raise ValueError(f"Unsupported decision '{decision}'. Use approve/deny or approve/reject.")

    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    body = {"status": status_value}
    if notes:
        body["notes"] = notes

    params = {"o": resolved_org_id}
    response_data = await client.put(
        f"/approvals/{approval_id}", json_data=body, params=params, api="console"
    )

    data = {
        "approval_id": approval_id,
        "decision": status_value,
        "notes": notes,
        "response": response_data,
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
    }

    return {
        "data": data,
        "metadata": metadata,
    }
