# MCP Compliance (2025-11-25)

## Response Structure

All workflow functions return this shape:
```python
{
    "data": {...},           # Primary payload
    "metadata": {
        "org_id": int,
        "pagination": {"has_more": bool, "cursor": str},
        "suggested_next_call": {"tool": str, "args": {...}},
        "notes": [str]
    }
}
```

## Pagination Pattern

Paginated endpoints must:
1. Accept `limit` and `page`/`cursor` parameters
2. Return `metadata.pagination.has_more`
3. Include `metadata.suggested_next_call` when more data exists

## Token Efficiency

- Default to summarized responses
- Provide `include_raw_*` flags for full payloads
- Use `max_*` parameters to cap list sizes (e.g., `max_stale_devices`)
