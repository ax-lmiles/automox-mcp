---
name: Validate MCP
description: Validate MCP server compliance with the 2025-11-25 specification. Use when checking compliance, auditing tools, or before releases.
---

# Validate MCP Compliance

## Run MCP Scanner

```bash
mcp-scanner \
  --stdio-command uv \
  --stdio-args run automox-mcp \
  --stdio-env AUTOMOX_API_KEY=test-api-key \
  --stdio-env AUTOMOX_ACCOUNT_UUID=test-account \
  --stdio-env AUTOMOX_ORG_ID=1 \
  --stdio-env AUTOMOX_MCP_SKIP_DOTENV=1 \
  --analyzers yara \
  --format summary
```

## Checklist

### Tools
- [ ] Every tool has comprehensive docstring
- [ ] All parameters have type hints
- [ ] Structured error responses
- [ ] Cursor-based pagination where applicable

### Resources
- [ ] `resource://domain/path` URI format
- [ ] Appropriate MIME types
- [ ] Clear descriptions

### Context Efficiency
- [ ] Default limits on responses
- [ ] Summary responses by default
- [ ] `include_raw_*` flags available
- [ ] `has_more` and `suggested_next_call` in pagination

### Security
- [ ] No credentials in responses
- [ ] Input sanitization
- [ ] Read-only mode enforced
