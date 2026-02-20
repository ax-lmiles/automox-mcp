# Automox API Quirks

Edge cases and gotchas when working with the Automox API.

## Dual API Endpoints

Automox has two separate API endpoints:

| API | Base URL | Use Cases |
|-----|----------|-----------|
| Console API | `console.automox.com/api` | Devices, policies, groups, webhooks |
| Policy Report API | `policyreport.automox.com` | Execution history, run results |

The client automatically handles fallback when console returns invalid JSON.

## ID Formats

Different APIs use different ID formats:

| Endpoint | ID Type | Example |
|----------|---------|---------|
| Console API | Integer | `/policies/12345?o=67890` |
| Policy Report API | UUID | `/policy-history/policies/a1b2c3d4-...` |

### Organization Resolution

Tools accept `org_id` (integer), but Policy Report API needs UUID:

```python
# Automatic resolution in utils/organization.py
org_uuid = await resolve_org_uuid(client, org_id)
```

Resolution order:
1. Explicit UUID if provided
2. Cached value on client
3. API lookup via `/orgs`
4. Fallback to account UUID

## Schedule Bitmasks

Automox uses a custom bitmask format for schedules:

| Day | Value |
|-----|-------|
| Monday | 2 |
| Tuesday | 4 |
| Wednesday | 8 |
| Thursday | 16 |
| Friday | 32 |
| Saturday | 64 |
| Sunday | 128 |

### Common Patterns

| Schedule | Bitmask |
|----------|---------|
| Weekdays | 62 (2+4+8+16+32) |
| Weekend | 192 (64+128) |
| Every day | 254 (all days) |

### Encoding Example

```python
# Monday + Wednesday + Friday
days = 2 + 8 + 32  # = 42
```

Full reference: `resource://policies/schedule-syntax`

## Query Parameter Patterns

Console API uses `o` for organization:

```
GET /policies?o=123456
GET /devices?o=123456&limit=100
```

Policy Report API uses path parameters:

```
GET /policy-history/policies/{uuid}/runs
```

## Rate Limits

Server enforces sliding window rate limits:

| API | Limit |
|-----|-------|
| Console API | 30 calls / 60 seconds |
| Policy Report API | 20 calls / 60 seconds |

Built-in `RateLimiter` class prevents exceeding limits.

## Error Handling

### API Errors

```python
class AutomoxAPIError(Exception):
    status_code: int
    message: str
    response_body: dict
```

### Rate Limit Errors

```python
class AutomoxRateLimitError(AutomoxAPIError):
    retry_after: int  # seconds
```

## Policy Types

| Type | Description |
|------|-------------|
| patch | Software patching |
| required_software | Software deployment |
| custom | Custom scripts |

## Filter Name Resolution

Console API accepts both filter IDs and names. The server normalizes filter names to IDs automatically via `resolve_filter_ids()`.

## Response Truncation

Large API responses may be truncated. Use pagination parameters:

```json
{
  "limit": 100,
  "page": 1
}
```

Check `metadata.pagination.has_more` for more pages.
