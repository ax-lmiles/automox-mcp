# Contributing to Automox MCP Server

Thank you for your interest in contributing!

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/AutomoxCommunity/automox-mcp.git
   cd automox-mcp
   ```

2. **Install dependencies** (repo pins Python 3.13)
   ```bash
   uv python install
   uv sync --python 3.13 --dev
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Automox credentials
   ```

## Development Workflow

### Running Tests

```bash
uv run --python 3.13 --dev pytest
```

### Interactive Testing

```bash
fastmcp dev
```
Opens MCP Inspector at http://localhost:6274

### Local Testing with Claude Code

```bash
claude mcp add automox-mcp uvx -- --from . --env-file .env automox-mcp
```

## Code Architecture

Follow the **Tool → Workflow** separation pattern:

| Layer | Location | Purpose |
|-------|----------|---------|
| Tools | `tools/*.py` | Thin wrappers with docstrings |
| Workflows | `workflows/*/*.py` | Business logic |
| Schemas | `schemas.py` | Pydantic models |

**Key rules:**
- No business logic in tool files
- Keep files under 500 lines
- All workflows return `{"data": {...}, "metadata": {...}}`

See `docs/reference/architecture.md` for details.

## Adding New Tools

1. Create workflow in `workflows/<domain>/*.py`
2. Add tool wrapper in `tools/<domain>_tools.py`
3. Export in `workflows/__init__.py`
4. Add tests in `tests/`

See `docs/guides/adding-tools.md` for the full guide.

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the architecture patterns

3. **Run tests** and ensure they pass
   ```bash
   uv run --python 3.13 --dev pytest
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "Add: brief description of change"
   ```

5. **Push and create PR**
   ```bash
   git push -u origin feature/your-feature-name
   ```

## Commit Message Format

Use prefixes for clarity:

| Prefix | Use Case |
|--------|----------|
| `Add:` | New features or tools |
| `Fix:` | Bug fixes |
| `Update:` | Enhancements to existing features |
| `Refactor:` | Code restructuring |
| `Docs:` | Documentation changes |
| `Test:` | Test additions or fixes |

## Code Style

- Use type hints for all function parameters and returns
- Write docstrings for public functions with `Args:` and `Returns:` sections
- Follow existing patterns in the codebase

## Questions?

Open a [GitHub Issue](https://github.com/AutomoxCommunity/automox-mcp/issues) for questions, bugs, or feature requests.
