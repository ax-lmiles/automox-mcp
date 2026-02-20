# Getting Started

This server implements the **MCP 2025-11-25 specification**.

## Prerequisites

- Python 3.11-3.13
- Automox account with API access
- `uv` package manager (recommended)

## Installation

```bash
# Clone and install
git clone https://github.com/AutomoxCommunity/automox-mcp.git
cd automox-mcp
uv sync --dev
```

## Configuration

Create a `.env` file with required variables:

```bash
AUTOMOX_API_KEY=your_api_key_here
AUTOMOX_ACCOUNT_UUID=your_account_uuid_here
AUTOMOX_ORG_ID=123456
```

### Optional Variables

```bash
# Enable read-only mode (22 of 36 tools)
AUTOMOX_MCP_READ_ONLY=true

# Load only specific modules
AUTOMOX_MCP_MODULES=devices,policies

# Skip .env file loading
AUTOMOX_MCP_SKIP_DOTENV=true
```

**When to use these:**

| Variable | Use Case |
|----------|----------|
| `AUTOMOX_MCP_READ_ONLY` | Auditing, monitoring, or demos where you want to prevent accidental changes |
| `AUTOMOX_MCP_MODULES` | Reduce token usage by loading only the tools you need (e.g., `devices,policies`) |
| `AUTOMOX_MCP_SKIP_DOTENV` | CI/CD pipelines or containers where env vars are injected externally |

## Running the Server

### Development Mode (MCP Inspector)

```bash
fastmcp dev
```

Opens interactive inspector at `localhost:6274`.

### Production Mode

```bash
uv run python -m automox_mcp.server
```

## First Tool Calls

### List Devices

```json
{
  "tool": "list_devices",
  "arguments": {
    "limit": 10
  }
}
```

### Check Device Health

```json
{
  "tool": "device_health_metrics",
  "arguments": {}
}
```

### Get Policy Catalog

```json
{
  "tool": "policy_catalog",
  "arguments": {
    "include_disabled": false
  }
}
```

## Running Tests

```bash
uv run --python 3.13 --dev pytest
```

## Next Steps

- [Architecture Overview](../reference/architecture.md) - Understand the codebase
- [Tool Reference](../api/tools.md) - Browse all 36 tools
- [Adding Tools](adding-tools.md) - Extend the server
