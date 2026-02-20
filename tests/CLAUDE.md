# Tests

## Commands

```bash
uv run --python 3.13 --dev pytest           # All tests
uv run --python 3.13 --dev pytest -k "test_name"  # Specific test
```

## File Naming

| Pattern | Purpose |
|---------|---------|
| `test_tools.py` | Tool registration, utilities |
| `test_workflows_*.py` | Workflow logic by domain |
| `test_config.py` | Environment configuration |
| `test_http.py` | HTTP client behavior |

## Patterns

- Use `@pytest.mark.asyncio` for async tests
- Mock `AutomoxClient` for workflow tests
- Tests don't require real API credentials
- FastMCP 2.x: `server.get_tools()` returns `dict` with tool names as keys
