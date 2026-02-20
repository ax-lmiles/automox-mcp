---
name: Add Tool
description: Add a new MCP tool to the Automox server. Use when creating new tools, adding API endpoints, or extending server capabilities.
---

# Add MCP Tool

Add a new tool following project patterns.

## Steps

1. **Create tool definition** in `tools/<module>_tools.py`:

```python
@mcp.tool()
async def tool_name(param1: str, param2: int | None = None) -> dict[str, Any]:
    """Brief description.

    Args:
        param1: Description
        param2: Optional description

    Returns:
        Dictionary with summary and data keys
    """
    return await workflow_function(param1, param2)
```

2. **Implement workflow** in `workflows/<module>.py`:

```python
async def workflow_function(param1: str, param2: int | None = None) -> dict[str, Any]:
    client = get_client()
    # API calls and processing
    return {"summary": "...", "data": [...], "metadata": {...}}
```

3. **Add tests** in `tests/test_<module>.py`

4. **Update README.md** with tool documentation

## Checklist

- [ ] Tool uses `verb_noun` naming
- [ ] Comprehensive docstring with Args/Returns
- [ ] Business logic in workflows, not tools
- [ ] Structured error responses
- [ ] Tests cover success and error cases
- [ ] README updated
