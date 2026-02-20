"""Policy workflows for Automox MCP.

This module provides workflows for managing Automox policies including:
- Catalog: List and describe policies
- Execution: Execute policies and view run history
- Approvals: Manage patch approvals
- Mutations: Create and update policies
"""

from __future__ import annotations

# Re-export all public functions for backward compatibility
from .approvals import resolve_patch_approval, summarize_patch_approvals
from .catalog import describe_policy, summarize_policies
from .execution import (
    describe_policy_run_result,
    execute_policy,
    summarize_policy_activity,
    summarize_policy_execution_history,
)
from .helpers import (
    decode_schedule_days_bitmask,
    normalize_policy_operations_input,
    normalize_status,
    take,
)
from .mutations import apply_policy_changes

__all__ = [
    # Catalog
    "summarize_policies",
    "describe_policy",
    # Execution
    "summarize_policy_activity",
    "summarize_policy_execution_history",
    "describe_policy_run_result",
    "execute_policy",
    # Approvals
    "summarize_patch_approvals",
    "resolve_patch_approval",
    # Mutations
    "apply_policy_changes",
    # Helpers (exported for compatibility)
    "normalize_status",
    "normalize_policy_operations_input",
    "decode_schedule_days_bitmask",
    "take",
]
