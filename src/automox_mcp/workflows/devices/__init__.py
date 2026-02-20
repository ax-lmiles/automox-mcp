"""Device workflows for Automox MCP.

This module provides workflows for managing Automox devices including:
- Queries: List, search, and describe devices
- Health: Device health aggregation
- Commands: Execute commands on devices
"""

from __future__ import annotations

# Re-export all public functions for backward compatibility
from .commands import issue_device_command
from .health import summarize_device_health
from .queries import (
    describe_device,
    list_device_inventory,
    list_devices_needing_attention,
    search_devices,
)

__all__ = [
    # Queries
    "list_devices_needing_attention",
    "list_device_inventory",
    "describe_device",
    "search_devices",
    # Health
    "summarize_device_health",
    # Commands
    "issue_device_command",
]
