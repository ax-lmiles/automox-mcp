# MCP Resources

The server exposes 5 MCP resource endpoints for reference data.

## Policy Resources

### resource://policies/quick-start

Copy-paste templates for common policy types:

- Patch specific software by name
- Patch all software
- Windows security updates
- macOS/Linux security updates
- Custom command policies

**Usage:** Read this resource when creating new policies.

### resource://policies/schema

Complete policy creation schema with field descriptions:

```json
{
  "name": "string (required)",
  "policy_type": "patch | required_software | custom",
  "schedule_days": "[int] - bitmask days",
  "schedule_time": "HH:MM",
  "server_group_id": "int",
  "configuration": {
    "auto_patch": "bool",
    "auto_reboot": "bool",
    "...": "..."
  }
}
```

### resource://policies/schedule-syntax

Schedule bitmask reference:

| Day | Value |
|-----|-------|
| Monday | 2 |
| Tuesday | 4 |
| Wednesday | 8 |
| Thursday | 16 |
| Friday | 32 |
| Saturday | 64 |
| Sunday | 128 |

**Common shortcuts:**
- Weekdays = 62
- Weekend = 192
- Every day = 254

---

## Server Group Resources

### resource://servergroups/list

Live mapping of server group IDs to names:

```json
{
  "groups": [
    {"id": 12345, "name": "Production Servers"},
    {"id": 12346, "name": "Development"},
    {"id": 12347, "name": "Windows Workstations"}
  ]
}
```

**Usage:** Reference when specifying `server_group_id` in tools.

---

## Webhook Resources

### resource://webhooks/event-types

Catalog of 39 webhook event types:

| Category | Events |
|----------|--------|
| Device | `device.created`, `device.deleted`, `device.updated` |
| Policy | `policy.created`, `policy.executed`, `policy.failed` |
| Patch | `patch.installed`, `patch.failed`, `patch.approved` |
| Group | `servergroup.created`, `servergroup.deleted` |
| User | `user.invited`, `user.removed` |

Includes:
- Event names
- Delivery limits
- Payload schemas

---

## Accessing Resources

Resources are read-only reference data. Access via MCP resource protocol:

```python
# In MCP client
content = await client.read_resource("resource://policies/quick-start")
```

Resources are registered in `server.py` via FastMCP's `@server.resource()` decorator.
