"""Device query workflows - listing, detail, and search operations."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Literal
from uuid import UUID

from ...client import AutomoxClient
from .formatters import (
    extract_detail_facts,
    sanitize_raw_device_payload,
    summarize_policy_assignments,
    summarize_policy_status,
)
from .helpers import (
    SANITIZED_SEQUENCE_LIMIT,
    SANITIZED_STRING_LIMIT,
    count_failed_policies,
    format_device_display_name,
    normalize_status,
    summarize_device_common_fields,
)


async def list_devices_needing_attention(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    group_id: int | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Highlight devices that Automox flags as needing attention."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params = {"o": resolved_org_id, "limit": limit, "offset": 0}
    if group_id is not None:
        params["groupId"] = group_id

    report = await client.get("/reports/needs-attention", params=params, api="console")

    items = report.get("data") if isinstance(report, Mapping) else None
    devices: Sequence[Mapping[str, Any]] = items if isinstance(items, Sequence) else []

    curated_devices = []
    for item in devices:
        curated_devices.append(
            {
                "device_id": item.get("device_id") or item.get("id"),
                "device_name": format_device_display_name(item),
                "policy_status": item.get("policy_status") or item.get("status"),
                "pending_patches": item.get("pending_updates") or item.get("pending"),
                "last_check_in": item.get("last_check_in") or item.get("last_seen"),
                "server_group_id": item.get("server_group_id"),
            }
        )

    data = {
        "group_id": group_id,
        "device_count": len(curated_devices),
        "devices": curated_devices,
    }

    metadata = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "group_id": group_id,
        "requested_limit": limit,
    }

    return {
        "data": data,
        "metadata": metadata,
    }


async def list_device_inventory(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    group_id: int | None = None,
    limit: int = 25,
    include_unmanaged: bool = False,
    policy_status: str | None = None,
    managed: bool | None = None,
) -> dict[str, Any]:
    """Return a list of devices in the organization with optional filtering."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params = {"o": resolved_org_id}
    if group_id is not None:
        params["groupId"] = group_id
    if limit is not None:
        params["limit"] = limit

    payload = await client.get("/servers", params=params, api="console")
    devices: Sequence[Mapping[str, Any]] = payload if isinstance(payload, list) else []

    policy_status_filter = normalize_status(policy_status) if policy_status else None

    curated_devices = []
    for item in devices:
        summary_fields = summarize_device_common_fields(item)
        is_managed = summary_fields["is_managed"]

        if managed is not None and is_managed != managed:
            continue
        if not include_unmanaged and not is_managed:
            continue
        device_policy_status = summary_fields["policy_status"]
        if policy_status_filter and device_policy_status != policy_status_filter:
            continue

        curated_devices.append(
            {
                "device_id": item.get("id") or item.get("device_id"),
                "hostname": format_device_display_name(item),
                "managed": is_managed,
                "os": item.get("os_name") or item.get("platform"),
                "policy_status": device_policy_status,
                "policy_failures": count_failed_policies(item) or None,
                "pending_patches": summary_fields["pending_patches"],
                "needs_attention": summary_fields["needs_attention"],
                "last_check_in": summary_fields["last_check_in"],
                "server_group_id": item.get("server_group_id"),
            }
        )
        if len(curated_devices) >= limit:
            break

    preview = curated_devices[:limit]

    data = {
        "total_devices_returned": len(curated_devices),
        "devices": preview,
    }

    metadata = payload.get("metadata", {}) if isinstance(payload, Mapping) else {}
    metadata.update(
        {
            "deprecated_endpoint": False,
            "org_id": resolved_org_id,
            "group_id": group_id,
            "requested_limit": limit,
            "include_unmanaged": include_unmanaged,
            "filters": {
                "policy_status": policy_status_filter,
                "managed": managed,
            },
        }
    )

    return {
        "data": data,
        "metadata": metadata,
    }


async def describe_device(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    device_id: int,
    include_packages: bool = False,
    include_inventory: bool = True,
    include_queue: bool = True,
    include_raw_details: bool = False,
) -> dict[str, Any]:
    """Provide a consolidated view of an Automox device."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params = {
        "o": resolved_org_id,
        "includeDetails": 1,
        "includeServerEvents": 1,
        "includeNextPatchTime": 1,
    }
    device_response = await client.get(f"/servers/{device_id}", params=params, api="console")
    device_data: Mapping[str, Any] = device_response if isinstance(device_response, Mapping) else {}

    packages_preview: list[dict[str, Any]] = []
    inventory_summary: dict[str, Any] | None = None
    queue_preview: list[dict[str, Any]] = []

    if include_packages:
        pkg_params: dict[str, Any] = {"o": resolved_org_id, "limit": 10}
        packages_raw = await client.get(
            f"/servers/{device_id}/packages", params=pkg_params, api="console"
        )
        if isinstance(packages_raw, Sequence):
            packages_preview = [
                {
                    "name": pkg.get("name") or pkg.get("package_name"),
                    "version": pkg.get("version"),
                    "status": pkg.get("status"),
                }
                for pkg in packages_raw[:10]
                if isinstance(pkg, Mapping)
            ]

    if include_inventory:
        org_uuid_str = (
            device_data.get("org_uuid")
            or device_data.get("organization_uuid")
            or device_data.get("orgId")
        )
        device_uuid_str = device_data.get("device_uuid") or device_data.get("uuid")
        try:
            if org_uuid_str and device_uuid_str:
                org_uuid_val = UUID(str(org_uuid_str))
                device_uuid_uuid = UUID(str(device_uuid_str))
                path = f"/device-details/orgs/{org_uuid_val}/devices/{device_uuid_uuid}/inventory"
                inventory_raw = await client.get(path, api="console")
                if isinstance(inventory_raw, Mapping):
                    inventory_map: Mapping[str, Any] = inventory_raw
                    categories: list[dict[str, Any]] = []
                    for name, items in inventory_map.items():
                        entry: dict[str, Any] = {"name": name}
                        if isinstance(items, Sequence) and not isinstance(
                            items, (str, bytes, bytearray)
                        ):
                            entry["item_count"] = len(items)
                        elif isinstance(items, Mapping):
                            entry["item_count"] = len(items)
                        categories.append(entry)
                        if len(categories) >= 15:
                            break
                    inventory_summary = {
                        "total_categories": len(inventory_map),
                        "categories": categories,
                    }
        except (ValueError, TypeError):
            inventory_summary = None

    if include_queue:
        queue_params: dict[str, Any] = {"o": resolved_org_id}
        queue_raw = await client.get(
            f"/servers/{device_id}/queues", params=queue_params, api="console"
        )
        if isinstance(queue_raw, Sequence):
            queue_preview = [
                {
                    "command": item.get("command") or item.get("type"),
                    "scheduled_time": item.get("scheduled_time") or item.get("scheduledAt"),
                    "status": item.get("status"),
                }
                for item in queue_raw[:10]
                if isinstance(item, Mapping)
            ]

    policy_status_summary, policy_status_total = summarize_policy_status(
        device_data.get("policy_status")
    )
    policy_assignments_summary, policy_assignments_breakdown, policy_assignments_total = (
        summarize_policy_assignments(device_data.get("server_policies"))
    )
    detail_facts = extract_detail_facts(device_data.get("detail"))

    tags_preview: list[str] | None = None
    raw_tags = device_data.get("tags") or device_data.get("labels")
    if isinstance(raw_tags, Sequence) and not isinstance(raw_tags, (str, bytes, bytearray)):
        tags_preview = [str(tag) for tag in raw_tags[:SANITIZED_SEQUENCE_LIMIT]]
        if len(raw_tags) > SANITIZED_SEQUENCE_LIMIT:
            tags_preview.append(f"... {len(raw_tags) - SANITIZED_SEQUENCE_LIMIT} more")
    elif raw_tags is not None:
        tags_preview = [str(raw_tags)]

    ip_addresses_preview: list[str] | None = None
    for ip_key in ("ip_addrs", "ip_addrs_private"):
        raw_ips = device_data.get(ip_key)
        if isinstance(raw_ips, Sequence) and not isinstance(raw_ips, (str, bytes, bytearray)):
            ip_addresses_preview = [str(ip) for ip in raw_ips[:SANITIZED_SEQUENCE_LIMIT]]
            if len(raw_ips) > SANITIZED_SEQUENCE_LIMIT:
                ip_addresses_preview.append(f"... {len(raw_ips) - SANITIZED_SEQUENCE_LIMIT} more")
            break

    status_value: Any = device_data.get("status")
    if isinstance(status_value, Mapping):
        status_value = (
            status_value.get("policy_status")
            or status_value.get("device_status")
            or status_value.get("status")
        )

    core: dict[str, Any] = {"device_id": device_id}
    device_uuid_val = device_data.get("device_uuid") or device_data.get("uuid")
    if device_uuid_val:
        core["device_uuid"] = device_uuid_val

    display_name = format_device_display_name(device_data)
    if display_name:
        core["hostname"] = display_name

    os_name = device_data.get("os_name") or device_data.get("platform")
    if os_name:
        core["os"] = os_name

    os_version = device_data.get("os_version")
    if os_version:
        core["os_version"] = os_version

    agent_version = device_data.get("agent_version")
    if agent_version:
        core["agent_version"] = agent_version

    ip_address = device_data.get("ip_address")
    if ip_address:
        core["ip_address"] = ip_address

    if ip_addresses_preview:
        core["ip_addresses"] = ip_addresses_preview

    server_group_id = device_data.get("server_group_id")
    if server_group_id:
        core["server_group_id"] = server_group_id

    last_check_in = device_data.get("last_check_in")
    if last_check_in:
        core["last_check_in"] = last_check_in

    last_refresh_time = device_data.get("last_refresh_time")
    if last_refresh_time:
        core["last_refresh_time"] = last_refresh_time

    uptime = device_data.get("uptime")
    if uptime is not None:
        core["uptime"] = uptime

    next_patch_time = device_data.get("next_patch_time")
    if next_patch_time:
        core["next_patch_time"] = next_patch_time

    managed_value = device_data.get("managed")
    if managed_value is not None:
        core["managed"] = managed_value

    patch_status = device_data.get("patch_status") or device_data.get("patchStatus")
    if patch_status:
        core["patch_status"] = patch_status

    normalized_status = normalize_status(status_value)
    if normalized_status != "unknown":
        core["status"] = normalized_status

    if tags_preview:
        core["tags"] = tags_preview

    core["policy_status"] = policy_status_summary

    try:
        raw_payload_bytes = len(json.dumps(device_data))
    except (TypeError, ValueError):
        raw_payload_bytes = None

    if include_raw_details and device_data:
        raw_details = {
            "included": True,
            "notice": (
                "Payload sanitized: long strings truncated to "
                f"{SANITIZED_STRING_LIMIT} chars and sequences limited "
                f"to {SANITIZED_SEQUENCE_LIMIT} items."
            ),
            "payload": sanitize_raw_device_payload(device_data),
        }
    else:
        available_fields = sorted(device_data.keys()) if device_data else []
        raw_details = {
            "included": False,
            "available_fields": available_fields,
        }

    data: dict[str, Any] = {
        "core": core,
        "software_preview": packages_preview,
        "inventory_overview": inventory_summary,
        "pending_commands": queue_preview,
        "policy_assignments": {
            "total": policy_assignments_total,
            "truncated": policy_assignments_total > len(policy_assignments_summary),
            "status_breakdown": dict(policy_assignments_breakdown),
            "policies": policy_assignments_summary,
        },
        "raw_details": raw_details,
    }

    if detail_facts:
        data["device_facts"] = detail_facts

    metadata = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "device_id": device_id,
        "include_packages": include_packages,
        "include_inventory": include_inventory,
        "include_queue": include_queue,
        "include_raw_details": include_raw_details,
        "policy_status_total": policy_status_total,
        "policy_status_displayed": len(policy_status_summary),
        "policy_status_truncated": policy_status_total > len(policy_status_summary),
        "policy_assignments_total": policy_assignments_total,
        "policy_assignments_displayed": len(policy_assignments_summary),
        "policy_assignments_truncated": policy_assignments_total > len(policy_assignments_summary),
        "policy_assignments_status_breakdown": dict(policy_assignments_breakdown),
        "software_preview_count": len(packages_preview),
        "pending_commands_count": len(queue_preview),
        "device_facts_available": detail_facts is not None,
    }

    if inventory_summary:
        metadata["inventory_category_count"] = inventory_summary.get("total_categories")

    if raw_payload_bytes is not None:
        metadata["raw_payload_bytes"] = raw_payload_bytes

    return {
        "data": data,
        "metadata": metadata,
    }


async def search_devices(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    hostname_contains: str | None = None,
    ip_address: str | None = None,
    tag: str | None = None,
    patch_status: Literal["missing"] | None = None,
    severity: Sequence[str] | str | None = None,
    managed: bool | None = None,
    group_id: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search for devices using simple text and attribute filters."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    params: dict[str, Any] = {"o": resolved_org_id, "limit": min(limit, 500)}
    if group_id is not None:
        params["groupId"] = group_id
    if managed is not None:
        params["managed"] = 1 if managed else 0
    if patch_status is not None:
        params["patchStatus"] = patch_status
    severity_values: list[str] = []
    if isinstance(severity, str):
        severity_values = [severity]
    elif isinstance(severity, Sequence) and not isinstance(severity, (str, bytes, bytearray)):
        severity_values = [str(value) for value in severity]
    if severity_values:
        normalized_severity = [
            value.strip().lower() for value in severity_values if str(value).strip()
        ]
        if normalized_severity:
            params["filters[severity][]"] = normalized_severity
            severity_values = normalized_severity
        else:
            severity_values = []

    devices = await client.get("/servers", params=params, api="console")
    devices = devices if isinstance(devices, Sequence) else []

    filtered = []
    hostname_term = (hostname_contains or "").lower()
    ip_term = (ip_address or "").strip()
    tag_term = (tag or "").lower()

    for device in devices:
        if hostname_term:
            name = str(device.get("name") or device.get("hostname") or "").lower()
            custom_name = str(device.get("custom_name") or "").lower()
            if hostname_term not in name and hostname_term not in custom_name:
                continue

        if ip_term:
            ip = str(device.get("ip_address") or device.get("ipAddress") or "").strip()
            if ip != ip_term:
                continue

        if tag_term:
            tags = device.get("tags") or device.get("labels") or []
            tags_lower = {str(t).lower() for t in tags} if isinstance(tags, Sequence) else set()
            if tag_term not in tags_lower:
                continue

        filtered.append(device)
        if len(filtered) >= limit:
            break

    preview = []
    for item in filtered:
        preview.append(
            {
                "device_id": item.get("id") or item.get("device_id"),
                "hostname": format_device_display_name(item),
                "ip_address": item.get("ip_address"),
                "server_group_id": item.get("server_group_id"),
                "managed": item.get("managed"),
                "pending_patches": item.get("pending_patches"),
                "needs_attention": item.get("needs_attention"),
                "last_check_in": item.get("last_check_in"),
                "tags": item.get("tags") or item.get("labels"),
            }
        )

    metadata = {}
    metadata.update(
        {
            "deprecated_endpoint": False,
            "org_id": resolved_org_id,
            "group_id": group_id,
            "request_limit": limit,
            "filters": {
                "hostname_contains": hostname_contains,
                "ip_address": ip_address,
                "tag": tag,
                "patch_status": patch_status,
                "severity": severity_values if severity_values else None,
                "managed": managed,
            },
        }
    )

    data = {
        "matches": len(preview),
        "devices": preview,
    }

    return {
        "data": data,
        "metadata": metadata,
    }
