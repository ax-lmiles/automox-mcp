# Schemas Reference

Pydantic models for input validation and response typing.

## Base Classes

### ForbidExtraModel

Disallows unexpected parameters:

```python
class ForbidExtraModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

### Mixins

| Mixin | Purpose |
|-------|---------|
| `OrgIdContextMixin` | Optional org_id, excluded from payloads |
| `OrgIdRequiredMixin` | Required org_id |
| `AccountIdMixin` | Account-level scoping |
| `PaginationMixin` | Standard pagination (page, limit) |

## Response Models

### ToolResponse

Standard MCP response wrapper:

```python
class ToolResponse(BaseModel):
    data: dict[str, Any]
    metadata: ResponseMetadata
```

### ResponseMetadata

```python
class ResponseMetadata(BaseModel):
    org_id: int | None = None
    pagination: PaginationMetadata | None = None
    suggested_next_call: SuggestedCall | None = None
    notes: list[str] = []
```

### PaginationMetadata

```python
class PaginationMetadata(BaseModel):
    has_more: bool
    cursor: str | None = None
    total_count: int | None = None
```

## Input Parameter Classes

### Device Parameters

```python
class DeviceSearchParams(OrgIdContextMixin):
    hostname: str | None = None
    ip_address: str | None = None
    tag: str | None = None
    status: str | None = None
    limit: int = 50

class DeviceCommandParams(OrgIdContextMixin):
    device_id: int
    command: Literal["scan", "patch_all", "patch_specific", "reboot"]
    patch_id: int | None = None  # Required for patch_specific
```

### Policy Parameters

```python
class PolicyDetailParams(OrgIdContextMixin):
    policy_id: int
    include_raw_response: bool = False

class PolicyExecutionParams(OrgIdContextMixin):
    policy_id: int
    server_group_id: int | None = None
```

### Pagination Parameters

```python
class PaginationMixin(BaseModel):
    page: int = 1
    limit: int = 50
```

### Approval Parameters

```python
class PatchApprovalDecisionParams(OrgIdContextMixin):
    approval_id: int
    decision: Literal["approve", "reject"]
    reason: str | None = None
```

### Webhook Parameters

```python
class WebhookCreateParams(OrgIdContextMixin):
    name: str
    url: str
    event_types: list[str]
    enabled: bool = True

class WebhookUpdateParams(OrgIdContextMixin):
    webhook_id: int
    name: str | None = None
    url: str | None = None
    event_types: list[str] | None = None
    enabled: bool | None = None
```

### Audit Parameters

```python
class AuditTrailEventsParams(OrgIdContextMixin):
    user_email: str | None = None
    action_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int = 100
```

## Validation Rules

### Org ID Resolution

```python
# Tools accept org_id but fall back to environment
org_id = params.org_id or os.environ.get("AUTOMOX_ORG_ID")
```

### Field Constraints

```python
class ExampleParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=500)
    page: int = Field(default=1, ge=1)
    name: str = Field(min_length=1, max_length=255)
```

### Enum Validation

```python
command: Literal["scan", "patch_all", "patch_specific", "reboot"]
decision: Literal["approve", "reject"]
policy_type: Literal["patch", "required_software", "custom"]
```

## Usage in Tools

```python
@server.tool()
async def my_tool(
    device_id: int,
    command: Literal["scan", "patch_all"],
    org_id: int | None = None,
) -> dict[str, Any]:
    """Tool docstring."""
    # Parameters are validated by FastMCP
    ...
```

## Response Format Example

```json
{
  "data": {
    "devices": [...],
    "summary": "Found 42 devices"
  },
  "metadata": {
    "org_id": 123456,
    "pagination": {
      "has_more": true,
      "cursor": "page_2"
    },
    "suggested_next_call": {
      "tool": "list_devices",
      "args": {"page": 2, "limit": 50}
    },
    "notes": ["3 devices need attention"]
  }
}
```
