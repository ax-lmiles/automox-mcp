# Architecture Rules

## Tool → Workflow Pattern

Tools in `tools/*.py` must be thin wrappers:
- Define MCP tool signature with docstring
- Delegate immediately to a workflow function
- NO business logic in tool files

Workflows in `workflows/*/` contain all business logic.

## Adding New Functionality

1. Add workflow function in appropriate `workflows/<domain>/*.py`
2. Add tool wrapper in `tools/<domain>_tools.py`
3. Register in `tools/__init__.py` module map
4. Add tests in `tests/`

## File Size Limits

Keep files under 500 lines. The codebase was refactored to split:
- `workflows/policy/` - 6 modules (was 1,732 lines)
- `workflows/devices/` - 5 modules (was 1,211 lines)
