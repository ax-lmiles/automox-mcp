# Adding New Tools

Follow these steps to add new MCP tools to the server.

## Architecture Pattern

Tools follow a strict **Tool → Workflow** separation:

```
tools/*.py       → Thin wrappers (parameter validation, docstrings)
workflows/*.py   → Business logic (API calls, data transformation)
```

## Step 1: Create the Workflow

Add your workflow function in the appropriate `workflows/<domain>/` module.

```python
# workflows/devices/queries.py

async def my_new_workflow(
    client: AutomoxClient,
    *,
    org_id: int | None = None,
    some_param: str,
) -> dict[str, Any]:
    """
    Describe what this workflow does.

    Returns standard response format.
    """
    org_id = org_id or client.org_id

    # Make API call
    response = await client.get(f"/some/endpoint?o={org_id}")

    # Transform data
    result = transform_response(response)

    return {
        "data": result,
        "metadata": {
            "org_id": org_id,
            "notes": ["Any relevant observations"],
        }
    }
```

## Step 2: Export from Workflows

Add the function to `workflows/__init__.py`:

```python
from .devices.queries import my_new_workflow

__all__ = [
    # ... existing exports
    "my_new_workflow",
]
```

## Step 3: Create the Tool Wrapper

Add the tool in `tools/<domain>_tools.py`:

```python
# tools/device_tools.py

def register(server: FastMCP, read_only: bool = False) -> None:
    # ... existing tools

    @server.tool()
    async def my_new_tool(
        some_param: str,
        org_id: int | None = None,
    ) -> dict[str, Any]:
        """
        One-line description for MCP clients.

        Args:
            some_param: What this parameter does
            org_id: Organization ID (uses env default if omitted)
        """
        async with AutomoxClient() as client:
            return await my_new_workflow(
                client,
                org_id=org_id,
                some_param=some_param,
            )
```

## Step 4: Register the Module

Ensure your tool module is in `tools/__init__.py`:

```python
TOOL_MODULES = {
    "devices": ("device_tools", True),   # (module_name, has_writes)
    # ...
}
```

## Step 5: Add Tests

Create tests in `tests/test_workflows_<domain>.py`:

```python
@pytest.mark.asyncio
async def test_my_new_workflow(mock_client):
    mock_client.get.return_value = {"items": [...]}

    result = await my_new_workflow(
        mock_client,
        some_param="test",
    )

    assert "data" in result
    assert "metadata" in result
```

## Response Format

All workflows must return this structure:

```python
{
    "data": {...},           # Primary payload
    "metadata": {
        "org_id": int,
        "pagination": {      # If paginated
            "has_more": bool,
            "cursor": str,
        },
        "suggested_next_call": {  # If more data available
            "tool": str,
            "args": {...},
        },
        "notes": [str],      # Observations
    }
}
```

## File Size Limits

Keep files under 500 lines. If a workflow module grows too large, split it:

```
workflows/devices/
├── queries.py      # List, search, describe
├── health.py       # Aggregations
├── commands.py     # Actions
├── formatters.py   # Response formatting
└── helpers.py      # Utilities
```

## Read-Only vs Write Tools

Mark tools that modify state:

- **Read-only**: `list_*`, `get_*`, `search_*`, `describe_*`, `*_summary`
- **Write tools**: `create_*`, `update_*`, `delete_*`, `execute_*`, `apply_*`

Write tools are excluded when `AUTOMOX_MCP_READ_ONLY=true`.
