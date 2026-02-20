# Response Format

All workflow functions return a standardized response structure.

## Standard Structure

```json
{
  "data": {
    // Primary payload - varies by tool
  },
  "metadata": {
    "org_id": 123456,
    "pagination": {
      "has_more": false,
      "cursor": null,
      "total_count": 42
    },
    "suggested_next_call": {
      "tool": "list_devices",
      "args": {"page": 2, "limit": 50}
    },
    "notes": [
      "3 devices need attention",
      "2 policies failed recently"
    ]
  }
}
```

## Fields

### data

Primary payload containing the requested information. Structure varies by tool:

```json
// list_devices
{
  "devices": [...],
  "summary": "Found 42 devices"
}

// device_health_metrics
{
  "total_devices": 100,
  "healthy": 85,
  "needs_attention": 15,
  "breakdown": {...}
}

// policy_detail
{
  "policy": {...},
  "recent_runs": [...],
  "affected_devices": 25
}
```

### metadata.org_id

Organization ID used for the request.

### metadata.pagination

Present for paginated endpoints:

| Field | Type | Description |
|-------|------|-------------|
| `has_more` | bool | More results available |
| `cursor` | string | Cursor for next page (optional) |
| `total_count` | int | Total matching items (optional) |

### metadata.suggested_next_call

When `has_more` is true, suggests the next tool call:

```json
{
  "tool": "list_devices",
  "args": {
    "page": 2,
    "limit": 50,
    "org_id": 123456
  }
}
```

### metadata.notes

Array of observations or warnings:

```json
[
  "3 devices have pending patches",
  "Rate limit: 25/30 calls remaining",
  "Some devices excluded due to filters"
]
```

## Pagination Pattern

For paginated tools:

1. First call returns page 1
2. Check `metadata.pagination.has_more`
3. If true, use `metadata.suggested_next_call` for next page
4. Repeat until `has_more` is false

```python
# Example pagination loop
result = await list_devices(limit=50)
all_devices = result["data"]["devices"]

while result["metadata"]["pagination"]["has_more"]:
    next_call = result["metadata"]["suggested_next_call"]
    result = await list_devices(**next_call["args"])
    all_devices.extend(result["data"]["devices"])
```

## Error Responses

Errors are raised as exceptions, not returned in the response:

```python
class AutomoxAPIError(Exception):
    status_code: int
    message: str
    response_body: dict

class AutomoxRateLimitError(AutomoxAPIError):
    retry_after: int
```

Tool wrappers catch and format these for MCP clients.

## Token Efficiency

Responses are designed for token efficiency:

- Default to summarized data
- Use `include_raw_*` flags for full payloads
- Use `max_*` parameters to cap list sizes

```json
// Summarized (default)
{
  "device_count": 42,
  "healthy_count": 38
}

// With include_raw_devices=true
{
  "device_count": 42,
  "healthy_count": 38,
  "devices": [
    {"id": 1, "hostname": "...", ...},
    {"id": 2, "hostname": "...", ...}
  ]
}
```
