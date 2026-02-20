---
name: Test MCP
description: Run the test suite for Automox MCP server. Use when running tests, checking test coverage, or validating changes.
argument-hint: "[all|coverage|<test_file>]"
---

# Run Tests

## Commands

**Run all tests:**
```bash
uv run --python 3.13 --dev pytest
```

**Run specific file:**
```bash
uv run --python 3.13 --dev pytest tests/test_tools.py
```

**Run with coverage:**
```bash
uv run --python 3.13 --dev pytest --cov=src/automox_mcp --cov-report=term-missing
```

**Interactive testing:**
```bash
fastmcp dev
```
Opens MCP Inspector at http://localhost:6274

## Test Files

| File | Purpose |
|------|---------|
| `test_tools.py` | Tool registration |
| `test_workflows_*.py` | Workflow logic |
| `test_config.py` | Configuration |
| `test_http.py` | HTTP client |
