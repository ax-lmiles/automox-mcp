"""Policy execution and timeline workflows."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from ...client import AutomoxClient
from .helpers import normalize_status, take


async def summarize_policy_activity(
    client: AutomoxClient,
    *,
    org_uuid: UUID,
    window_days: int = 7,
    top_failures: int = 5,
    max_runs: int = 200,
) -> dict[str, Any]:
    """Aggregate policy activity for an organization over the requested window."""
    count_params = {"org": str(org_uuid), "days": window_days}
    run_counts = await client.get(
        "/policy-history/policy-run-count", params=count_params, api="policyreport"
    )

    run_params = {
        "org": str(org_uuid),
        "limit": max_runs,
        "sort": "run_time:desc",
    }
    if window_days:
        earliest_time = datetime.now(UTC) - timedelta(days=window_days)
        run_params["start_time"] = (
            earliest_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
    policy_runs = await client.get(
        "/policy-history/policy-runs", params=run_params, api="policyreport"
    )

    run_items = policy_runs.get("data") if isinstance(policy_runs, Mapping) else None
    runs: Sequence[Mapping[str, Any]] = run_items if isinstance(run_items, Sequence) else []

    status_counter: Counter[str] = Counter()
    policy_breakdown: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total_runs": 0, "failed_runs": 0}
    )

    for item in runs:
        status = normalize_status(item.get("result_status") or item.get("status"))
        status_counter[status] += 1

        policy_key = str(
            item.get("policy_uuid") or item.get("policy_id") or item.get("policy_name") or "unknown"
        )
        entry = policy_breakdown[policy_key]
        entry["policy_uuid"] = item.get("policy_uuid") or entry.get("policy_uuid")
        entry["policy_name"] = item.get("policy_name") or entry.get("policy_name") or policy_key
        entry["total_runs"] += 1
        if status not in {"success"}:
            entry["failed_runs"] += 1

    top_failures_list = sorted(
        (
            {
                "policy_uuid": entry.get("policy_uuid"),
                "policy_name": entry.get("policy_name"),
                "failed_runs": entry["failed_runs"],
                "total_runs": entry["total_runs"],
                "failure_rate": entry["failed_runs"] / entry["total_runs"]
                if entry["total_runs"]
                else 0.0,
            }
            for entry in policy_breakdown.values()
            if entry["failed_runs"] > 0
        ),
        key=lambda item: (item["failed_runs"], item["total_runs"]),
        reverse=True,
    )[:top_failures]

    raw_counts_data = None
    if isinstance(run_counts, Mapping):
        raw_counts_data = run_counts.get("data")

    overview = {
        "window_days": window_days,
        "total_runs_considered": len(runs),
        "status_breakdown": dict(status_counter),
        "top_failing_policies": top_failures_list,
        "recent_runs": list(take(runs, 10)),
        "raw_counts": raw_counts_data,
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_uuid": str(org_uuid),
        "window_days": window_days,
        "total_runs_considered": len(runs),
    }

    return {
        "data": overview,
        "metadata": metadata,
    }


async def summarize_policy_execution_history(
    client: AutomoxClient,
    *,
    org_uuid: UUID,
    policy_uuid: UUID,
    report_days: int | None = 7,
    limit: int = 50,
) -> dict[str, Any]:
    """Return a concise execution timeline for a specific policy."""
    params: dict[str, Any] = {
        "org": str(org_uuid),
        "policy_uuid": str(policy_uuid),
        "sort": "-started_at",
    }
    if report_days is not None:
        params["report_days"] = report_days

    path = f"/policy-history/policies/{policy_uuid}/runs"
    payload = await client.get(path, params=params, api="policyreport")
    runs: Sequence[Mapping[str, Any]] = []
    policy_name: Any = None

    if isinstance(payload, Mapping):
        candidate_sequences = (
            seq
            for seq in (
                payload.get("runs"),
                payload.get("items"),
                payload.get("data"),
            )
            if isinstance(seq, Sequence)
        )
        runs = next(candidate_sequences, [])
        policy_name = payload.get("policy_name") or payload.get("name")
    elif isinstance(payload, Sequence):
        runs = payload

    runs = list(take(runs, limit))

    status_counter: Counter[str] = Counter()
    timeline = []

    for item in runs:
        status = normalize_status(item.get("result_status") or item.get("status"))
        status_counter[status] += 1
        timeline.append(
            {
                "exec_token": item.get("exec_token") or item.get("execution_token"),
                "started_at": item.get("started_at") or item.get("start_time"),
                "completed_at": item.get("completed_at") or item.get("end_time"),
                "status": status,
                "device_failures": item.get("device_failures") or item.get("failed_devices"),
                "summary": item.get("summary"),
            }
        )

    data = {
        "policy_uuid": str(policy_uuid),
        "policy_name": policy_name,
        "report_days": report_days,
        "status_breakdown": dict(status_counter),
        "recent_executions": timeline,
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_uuid": str(org_uuid),
        "policy_uuid": str(policy_uuid),
        "report_days": report_days,
        "run_count": len(timeline),
    }

    return {
        "data": data,
        "metadata": metadata,
    }


async def describe_policy_run_result(
    client: AutomoxClient,
    *,
    org_uuid: UUID,
    policy_uuid: UUID,
    exec_token: UUID,
    sort: str | None = None,
    result_status: str | None = None,
    device_name: str | None = None,
    page: int | None = None,
    limit: int | None = None,
    max_output_length: int | None = None,
) -> dict[str, Any]:
    """Retrieve per-device results for a specific policy execution."""
    params: dict[str, Any] = {"org": str(org_uuid)}
    if sort:
        params["sort"] = sort
    if result_status:
        params["result_status"] = result_status
    if device_name:
        params["device_name"] = device_name
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    if max_output_length is not None:
        params["max_output_length"] = max_output_length

    path = f"/policy-history/policies/{policy_uuid}/{exec_token}"
    payload = await client.get(path, params=params, api="policyreport")

    devices_raw: Sequence[Mapping[str, Any]] = []
    pagination_meta: Mapping[str, Any] | None = None
    if isinstance(payload, Mapping):
        data_section = payload.get("data")
        if isinstance(data_section, Sequence):
            devices_raw = data_section
        meta_section = payload.get("metadata")
        if isinstance(meta_section, Mapping):
            pagination_meta = meta_section
    elif isinstance(payload, Sequence):
        devices_raw = payload

    status_counter: Counter[str] = Counter()
    device_results: list[dict[str, Any]] = []

    for entry in devices_raw:
        if not isinstance(entry, Mapping):
            continue
        status = normalize_status(entry.get("result_status"))
        status_counter[status] += 1
        device_results.append(
            {
                "device_id": entry.get("device_id"),
                "device_uuid": entry.get("device_uuid"),
                "hostname": entry.get("hostname"),
                "custom_name": entry.get("custom_name"),
                "display_name": entry.get("display_name"),
                "result_status": status,
                "result_reason": entry.get("result_reason") or entry.get("result-reason"),
                "run_time": entry.get("run_time"),
                "event_time": entry.get("event_time"),
                "stdout": entry.get("stdout"),
                "stderr": entry.get("stderr"),
                "exit_code": entry.get("exit_code") or entry.get("error_code"),
                "patches": entry.get("patches"),
                "device_deleted_at": entry.get("device_deleted_at"),
            }
        )

    data = {
        "policy_uuid": str(policy_uuid),
        "exec_token": str(exec_token),
        "result_summary": {
            "total_devices": len(device_results),
            "status_breakdown": dict(status_counter),
        },
        "devices": device_results,
        "pagination": pagination_meta,
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_uuid": str(org_uuid),
        "policy_uuid": str(policy_uuid),
        "exec_token": str(exec_token),
        "result_count": len(device_results),
        "status_breakdown": dict(status_counter),
        "page": pagination_meta.get("current_page") if pagination_meta else None,
        "limit": pagination_meta.get("limit") if pagination_meta else limit,
        "total_count": pagination_meta.get("total_count") if pagination_meta else None,
    }

    return {
        "data": data,
        "metadata": metadata,
    }


async def execute_policy(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    policy_id: int,
    action: str,
    device_id: int | None = None,
) -> dict[str, Any]:
    """Execute an Automox policy immediately for remediation."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    normalized_action = action.strip()
    alias_map = {
        "remediateDevice": "remediateServer",
        "remediatedevice": "remediateServer",
    }
    effective_action = alias_map.get(normalized_action, normalized_action)

    if effective_action not in {"remediateAll", "remediateServer"}:
        raise ValueError(
            f"Invalid action '{action}'. Use 'remediateAll' for all devices or "
            f"'remediateDevice' for a specific device."
        )

    if effective_action == "remediateServer" and device_id is None:
        raise ValueError("device_id is required when action is 'remediateDevice'")

    body: dict[str, Any] = {"action": effective_action}
    if device_id is not None:
        body["serverId"] = device_id

    params = {"o": resolved_org_id}
    response_data = await client.post(
        f"/policies/{policy_id}/action", json_data=body, params=params, api="console"
    )

    data = {
        "policy_id": policy_id,
        "action": effective_action,
        "device_id": device_id,
        "execution_initiated": True,
        "response": response_data,
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "policy_id": policy_id,
    }

    return {
        "data": data,
        "metadata": metadata,
    }
