# Automox MCP Server

FastMCP server exposing 36 workflow tools for Automox endpoint management.

## Reference Docs (read on-demand)

- `docs/guides/getting-started.md` - Installation and first steps
- `docs/guides/adding-tools.md` - How to add new MCP tools
- `docs/guides/examples.md` - Real-world usage examples
- `docs/reference/architecture.md` - System design and patterns
- `docs/reference/api-quirks.md` - Automox API edge cases
- `docs/reference/schemas.md` - Pydantic models and validation
- `docs/api/tools.md` - All 36 tools by category
- `docs/api/response-format.md` - Standard response structure

## Commands

```bash
uv run --python 3.13 --dev pytest   # Run tests
fastmcp dev                          # MCP Inspector at localhost:6274
```

## Critical Rules

- **Tool → Workflow separation** - No business logic in `tools/*.py`
- **File size limit** - Keep files under 500 lines
- **Response format** - All workflows return `{"data": {...}, "metadata": {...}}`

## API Quirks

- **Dual endpoints** - Console API (integer IDs) vs Policy Report API (UUIDs)
- **Org resolution** - Tools fall back to `AUTOMOX_ORG_ID` env var
- **Schedule bitmasks** - Mon=2, Tue=4, Wed=8... (see `docs/reference/api-quirks.md`)
