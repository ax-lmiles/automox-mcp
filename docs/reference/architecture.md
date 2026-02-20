# Architecture

## Overview

The Automox MCP Server follows a layered architecture:

```
┌─────────────────────────────────────────────┐
│              MCP Protocol Layer             │
│            (FastMCP + stdio)                │
├─────────────────────────────────────────────┤
│               Tools Layer                   │
│    (tools/*.py - thin wrappers)             │
├─────────────────────────────────────────────┤
│             Workflows Layer                 │
│    (workflows/*/*.py - business logic)      │
├─────────────────────────────────────────────┤
│              Client Layer                   │
│         (client.py - HTTP)                  │
├─────────────────────────────────────────────┤
│            Automox APIs                     │
│   (console.automox.com, policyreport.*)     │
└─────────────────────────────────────────────┘
```

## Directory Structure

```
src/automox_mcp/
├── server.py           # Entry point, FastMCP setup
├── client.py           # HTTP client (dual-endpoint)
├── schemas.py          # Pydantic models (890 lines)
├── tools/              # Tool registration (1,664 lines)
│   ├── __init__.py     # Module registry
│   ├── device_tools.py
│   ├── policy_tools.py
│   ├── webhook_tools.py
│   ├── group_tools.py
│   ├── account_tools.py
│   ├── package_tools.py
│   ├── report_tools.py
│   ├── audit_tools.py
│   └── event_tools.py
├── workflows/          # Business logic (4,814 lines)
│   ├── __init__.py     # Public exports
│   ├── account.py
│   ├── audit.py
│   ├── events.py
│   ├── groups.py
│   ├── packages.py
│   ├── reports.py
│   ├── webhooks.py
│   ├── devices/        # Device workflows (5 modules)
│   │   ├── queries.py
│   │   ├── health.py
│   │   ├── commands.py
│   │   ├── formatters.py
│   │   └── helpers.py
│   └── policy/         # Policy workflows (6 modules)
│       ├── catalog.py
│       ├── execution.py
│       ├── approvals.py
│       ├── mutations.py
│       ├── payload.py
│       └── helpers.py
├── resources/          # MCP resources
│   ├── policy_resources.py
│   ├── servergroup_resources.py
│   └── webhook_resources.py
└── utils/
    ├── organization.py # org_id → UUID resolution
    └── tooling.py      # Rate limiting, formatting
```

## Key Components

### Server (`server.py`)

- FastMCP initialization with instructions
- Tool and resource registration
- Environment validation
- Stdio transport patching

### Client (`client.py`)

`AutomoxClient` provides async HTTP access to two Automox APIs:

| Endpoint | Base URL | Usage |
|----------|----------|-------|
| Console API | `console.automox.com/api` | General operations |
| Policy Report API | `policyreport.automox.com` | Execution history |

Features:
- Bearer token authentication
- 15-second timeout
- Auto-fallback between endpoints
- Custom error types (`AutomoxAPIError`, `AutomoxRateLimitError`)

### Tools (`tools/`)

Tools are thin wrappers that:
1. Define MCP tool signature with docstring
2. Validate parameters via Pydantic
3. Delegate to workflow functions
4. Return standardized responses

**No business logic in tool files.**

### Workflows (`workflows/`)

Workflows contain all business logic:
- API calls via client
- Data transformation
- Response formatting
- Error handling

### Schemas (`schemas.py`)

Pydantic models for:
- Input validation (tool parameters)
- Output typing (response structures)
- Shared mixins (org_id, pagination)

### Resources (`resources/`)

MCP resources provide reference data:
- `resource://policies/quick-start` - Policy templates
- `resource://policies/schema` - Policy creation schema
- `resource://policies/schedule-syntax` - Bitmask reference
- `resource://servergroups/list` - Group ID mapping
- `resource://webhooks/event-types` - Event catalog

## Design Principles

1. **Separation of Concerns**: Tools ≠ Workflows
2. **File Size Limits**: Max 500 lines per file
3. **Standard Responses**: All workflows return `{data, metadata}`
4. **Pagination Support**: `has_more` flag + `suggested_next_call`
5. **Rate Limiting**: Client-side enforcement
6. **Read-Only Mode**: Environment-controlled tool filtering
