# Tool Reference

All 36 MCP tools organized by category.

## Devices (6 tools)

| Tool | Type | Description |
|------|------|-------------|
| `list_devices` | Query | List devices with filtering and pagination |
| `device_detail` | Query | Get detailed info for a single device |
| `devices_needing_attention` | Query | Find devices flagged for action |
| `search_devices` | Query | Search by hostname, IP, tag, or status |
| `device_health_metrics` | Aggregation | Fleet-wide health summary |
| `execute_device_command` | Action | Issue scan, patch, or reboot commands |

### list_devices

```json
{
  "limit": 50,
  "page": 1,
  "group_id": null,
  "org_id": null
}
```

### execute_device_command

```json
{
  "device_id": 12345,
  "command": "scan | patch_all | patch_specific | reboot",
  "patch_id": null
}
```

---

## Policies (9 tools)

| Tool | Type | Description |
|------|------|-------------|
| `policy_catalog` | Query | List all policies |
| `policy_detail` | Query | Get single policy details |
| `policy_health_overview` | Aggregation | Policy status summary |
| `policy_execution_timeline` | Query | Recent execution history |
| `policy_run_results` | Query | Per-device execution results |
| `execute_policy_now` | Action | Execute policy immediately |
| `apply_policy_changes` | Mutation | Create or update policies |
| `patch_approvals_summary` | Query | Pending approval overview |
| `decide_patch_approval` | Mutation | Approve or reject patches |

### apply_policy_changes

```json
{
  "name": "Policy Name",
  "policy_type": "patch | required_software | custom",
  "schedule_days": [1, 3, 5],
  "schedule_time": "02:00",
  "server_group_id": 12345,
  "policy_id": null
}
```

---

## Server Groups (5 tools)

| Tool | Type | Description |
|------|------|-------------|
| `list_server_groups` | Query | List all server groups |
| `get_server_group` | Query | Get single group details |
| `create_server_group` | Mutation | Create new group |
| `update_server_group` | Mutation | Modify existing group |
| `delete_server_group` | Deletion | Remove group |

### create_server_group

```json
{
  "name": "Group Name",
  "parent_id": null,
  "policies": [],
  "org_id": null
}
```

---

## Webhooks (8 tools)

| Tool | Type | Description |
|------|------|-------------|
| `list_webhook_event_types` | Query | Available event types |
| `list_webhooks` | Query | List configured webhooks |
| `get_webhook` | Query | Get webhook details |
| `create_webhook` | Mutation | Create new webhook |
| `update_webhook` | Mutation | Modify webhook |
| `delete_webhook` | Deletion | Remove webhook |
| `test_webhook` | Action | Send test payload |
| `rotate_webhook_secret` | Mutation | Regenerate HMAC secret |

### create_webhook

```json
{
  "name": "My Webhook",
  "url": "https://example.com/webhook",
  "event_types": ["device.created", "policy.executed"],
  "enabled": true,
  "org_id": null
}
```

---

## Packages (2 tools)

| Tool | Type | Description |
|------|------|-------------|
| `list_device_packages` | Query | Packages on a specific device |
| `search_org_packages` | Query | Search packages across org |

### search_org_packages

```json
{
  "query": "chrome",
  "limit": 50,
  "org_id": null
}
```

---

## Reports (2 tools)

| Tool | Type | Description |
|------|------|-------------|
| `prepatch_report` | Query | Pre-patch compliance status |
| `noncompliant_report` | Query | Non-compliant devices |

---

## Events (1 tool)

| Tool | Type | Description |
|------|------|-------------|
| `list_events` | Query | Organization event log |

### list_events

```json
{
  "limit": 100,
  "page": 1,
  "org_id": null
}
```

---

## Account (2 tools)

| Tool | Type | Description |
|------|------|-------------|
| `invite_user_to_account` | Mutation | Send user invitation |
| `remove_user_from_account` | Deletion | Remove user access |

### invite_user_to_account

```json
{
  "email": "user@example.com",
  "role": "admin | user | viewer",
  "org_id": null
}
```

---

## Audit (1 tool)

| Tool | Type | Description |
|------|------|-------------|
| `audit_trail_user_activity` | Query | User action audit trail |

### audit_trail_user_activity

```json
{
  "user_email": null,
  "action_type": null,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "limit": 100,
  "org_id": null
}
```

---

## Read-Only Mode

When `AUTOMOX_MCP_READ_ONLY=true`, only 22 tools are available:

**Excluded (write tools):**
- `execute_device_command`
- `apply_policy_changes`
- `execute_policy_now`
- `decide_patch_approval`
- `create_server_group`
- `update_server_group`
- `delete_server_group`
- `create_webhook`
- `update_webhook`
- `delete_webhook`
- `test_webhook`
- `rotate_webhook_secret`
- `invite_user_to_account`
- `remove_user_from_account`
