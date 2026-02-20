---
name: Documentation
description: Create and maintain CLAUDE.md files and project documentation following Claude Code best practices. Use when writing documentation, updating existing docs, or ensuring documentation consistency.
---

# Documentation Skill

Key principle: *"Would removing this cause Claude to make mistakes? If not, cut it."*

## References

- Best practices: https://docs.anthropic.com/en/docs/claude-code/memory
- Templates and patterns: `reference.md` (in this skill folder)

## Context Rules

| Do | Don't |
|----|-------|
| Keep CLAUDE.md concise (50-80 lines) | Write verbose explanations |
| Plain paths for large docs (100+ lines) | `@` import large reference docs |
| Repeated rules → `.claude/rules/` | Duplicate across files |
| Document constraints/gotchas | Document what code shows |

## CLAUDE.md Content

**Include:** Commands Claude can't guess, constraints that prevent bugs, gotchas

**Exclude:** Info Claude can infer, standard conventions, detailed API docs

## @ Import Rules

- `@path` = loads immediately into context
- Plain path = read on-demand
- Use `@` only for files < 50 lines

## Path-Scoped Rules

Add `paths:` frontmatter to `.claude/rules/*.md` for directory-specific rules:
```yaml
paths: ["src/api/**/*"]
```

## Steps

1. Check existing CLAUDE.md files for patterns
2. Read root CLAUDE.md for project conventions
3. Identify constraints that prevent mistakes
4. Draft content, then prune aggressively
5. Move repeated rules to `.claude/rules/`
