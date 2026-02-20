# Security Rules

## API Key Handling

The `AUTOMOX_API_KEY` is loaded in `server.py` via `_validate_env()`.
Never include it in:
- Tool responses
- Error messages
- Log output

## Read-Only Mode

When `AUTOMOX_MCP_READ_ONLY=true`:
- Only read-only tools are registered (22 of 36)
- Checked in `tools/__init__.py` via `register_tools()`
- Write tools: `execute_*`, `apply_*`, `create_*`, `update_*`, `delete_*`

## Destructive Operations

Tools that modify Automox state require confirmation patterns:
- `execute_device_command` - Issues scan/patch/reboot
- `apply_policy_changes` - Creates/updates policies
- `delete_server_group` - Permanent deletion
