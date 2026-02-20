---
name: Refactor Monolith
description: Refactor large monolithic files into smaller modules. Use when splitting large files, improving code organization, or reducing context overhead.
argument-hint: "[file_path]"
---

# Refactor Monolithic Code

Files >500 lines should be reviewed for refactoring.

## Find Large Files

```bash
find src -name "*.py" -exec wc -l {} + | sort -rn | head -20
```

## Target Structure

Convert `module.py` → `module/` with: `__init__.py` (re-exports), `queries.py`, `mutations.py`, `helpers.py`, `formatters.py`

## Steps

1. **Analyze** - Group functions by responsibility
2. **Create directory** - `mkdir module/`
3. **Split files** - Move related functions to sub-modules
4. **Re-export** - Update `__init__.py` for backward compatibility
5. **Update imports** - Fix any broken imports
6. **Test** - Run full test suite

## Grouping Guidelines

| Category | Functions | File |
|----------|-----------|------|
| Read ops | `list_*`, `get_*`, `search_*` | `queries.py` |
| Write ops | `create_*`, `update_*`, `delete_*` | `mutations.py` |
| Utilities | `_helper_*`, `format_*` | `helpers.py` |
| Types | Classes, enums, type aliases | `types.py` |

## Checklist

- [ ] No file exceeds 500 lines
- [ ] Public API unchanged (backward compatible)
- [ ] All tests pass
- [ ] Imports updated throughout codebase
