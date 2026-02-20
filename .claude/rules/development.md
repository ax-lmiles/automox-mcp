# Development Rules

## Environment Setup

Required in `.env`:
```
AUTOMOX_API_KEY=...
AUTOMOX_ACCOUNT_UUID=...
AUTOMOX_ORG_ID=123456
```

Optional:
```
AUTOMOX_MCP_READ_ONLY=true
AUTOMOX_MCP_MODULES=devices,policies
```

## Automox API Quirks

- **Console API** uses integer IDs: `/policies/{id}?o={org_id}`
- **Policy Report API** uses UUIDs: `/policy-history/policies/{uuid}/runs`
- **Schedule bitmasks**: Days use trailing-zero pattern (Mon=2, Tue=4, Wed=8...)
- **Org UUID resolution**: Use `utils.resolve_org_uuid()` to convert org_id → UUID

## Common Patterns

Workflow functions should:
1. Resolve `org_id` via `org_id or client.org_id`
2. Build params dict for API call
3. Transform response into standard format
4. Return `{"data": ..., "metadata": ...}`
