"""Policy create/update mutation workflows."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from ...client import AutomoxAPIError, AutomoxClient
from .helpers import extract_policy_id_from_response, normalize_policy_operations_input
from .payload import prepare_policy_payload_for_create, prepare_policy_payload_for_update

logger = logging.getLogger(__name__)


async def apply_policy_changes(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    operations: Sequence[Mapping[str, Any]],
    preview: bool = False,
) -> dict[str, Any]:
    """Create or update Automox policies from structured change requests."""
    resolved_org_id = org_id or client.org_id
    if not resolved_org_id:
        raise ValueError("org_id required - pass explicitly or set AUTOMOX_ORG_ID")

    normalized_operations = normalize_policy_operations_input(operations)
    results: list[dict[str, Any]] = []

    for index, operation in enumerate(normalized_operations):
        action = str(operation.get("action") or "").strip().lower()
        if action not in {"create", "update"}:
            raise ValueError(
                f"Operation at index {index} has unsupported action '{operation.get('action')}'."
            )

        raw_policy = operation.get("policy")
        if not isinstance(raw_policy, Mapping):
            raise ValueError(f"Operation at index {index} is missing a 'policy' object.")

        entry: dict[str, Any] = {
            "index": index,
            "action": action,
        }

        if action == "create":
            payload, payload_warnings = prepare_policy_payload_for_create(
                raw_policy, org_id=resolved_org_id
            )
            entry["policy_name"] = payload.get("name")
            entry["policy_type_name"] = payload.get("policy_type_name")
            entry["request"] = {
                "method": "POST",
                "path": "/policies",
                "params": {"o": resolved_org_id},
                "body": payload,
            }
            if payload_warnings:
                entry.setdefault("warnings", []).extend(payload_warnings)

            if preview:
                entry["status"] = "preview"
            else:
                response_data = await client.post(
                    "/policies",
                    json_data=payload,
                    params={"o": resolved_org_id},
                    api="console",
                )
                entry["status"] = "created"
                entry["response"] = response_data
                policy_id = extract_policy_id_from_response(response_data)
                if policy_id is not None:
                    entry["policy_id"] = policy_id
                    try:
                        latest_policy = await client.get(
                            f"/policies/{policy_id}",
                            params={"o": resolved_org_id},
                            api="console",
                        )
                        if isinstance(latest_policy, Mapping):
                            entry["policy"] = latest_policy
                    except (AutomoxAPIError, ValueError, TypeError, KeyError) as exc:
                        logger.debug("Failed to fetch created policy %s: %s", policy_id, exc)
                        entry.setdefault("warnings", []).append(
                            f"Created policy {policy_id}, but failed to retrieve latest state."
                        )
                else:
                    entry["policy_id"] = None

        else:  # update
            policy_id_value = operation.get("policy_id")
            if policy_id_value is None:
                raise ValueError(f"Operation at index {index} requires policy_id for updates.")
            try:
                policy_id = int(policy_id_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Operation at index {index} has invalid policy_id '{policy_id_value}'."
                ) from exc

            merge_flag_raw = operation.get("merge_existing")
            merge_existing = True if merge_flag_raw is None else bool(merge_flag_raw)

            payload, previous_policy, payload_warnings = await prepare_policy_payload_for_update(
                client,
                policy_id,
                raw_policy,
                org_id=resolved_org_id,
                merge_existing=merge_existing,
            )

            entry["policy_id"] = policy_id
            entry["policy_name"] = payload.get("name")
            entry["policy_type_name"] = payload.get("policy_type_name")
            if previous_policy is not None:
                entry["previous_policy"] = previous_policy
            if payload_warnings:
                entry.setdefault("warnings", []).extend(payload_warnings)

            entry["request"] = {
                "method": "PUT",
                "path": f"/policies/{policy_id}",
                "params": {"o": resolved_org_id},
                "body": payload,
            }

            if preview:
                entry["status"] = "preview"
            else:
                response_data = await client.put(
                    f"/policies/{policy_id}",
                    json_data=payload,
                    params={"o": resolved_org_id},
                    api="console",
                )
                entry["status"] = "updated"
                entry["response"] = response_data
                try:
                    latest_policy = await client.get(
                        f"/policies/{policy_id}",
                        params={"o": resolved_org_id},
                        api="console",
                    )
                    if isinstance(latest_policy, Mapping):
                        entry["policy"] = latest_policy
                except (AutomoxAPIError, ValueError, TypeError, KeyError) as exc:
                    logger.debug("Failed to fetch updated policy %s: %s", policy_id, exc)
                    entry.setdefault("warnings", []).append(
                        f"Updated policy {policy_id}, but failed to retrieve latest state."
                    )

        results.append(entry)

    data = {
        "operations": results,
        "preview": preview,
    }
    metadata = {
        "deprecated_endpoint": False,
        "org_id": resolved_org_id,
        "operation_count": len(results),
        "preview": preview,
    }
    return {
        "data": data,
        "metadata": metadata,
    }
