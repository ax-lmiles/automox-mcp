---
name: Clauditor
description: Audit Claude configuration files against Anthropic best practices. Use to validate CLAUDE.md files, rules, and skills before committing.
---

# Clauditor - Claude Config Auditor

Audit all Claude configuration files against best practices.

## Quick Audit

```bash
# Find all Claude config files
find . -name "CLAUDE.md" -o -name "*.md" -path "*/.claude/*" | head -20

# Check by lines
wc -l $(find . -name "CLAUDE.md") .claude/rules/*.md .claude/skills/*/SKILL.md 2>/dev/null

# Check by tokens (chars/4)
for f in $(find . -name "CLAUDE.md" -o -path "*/.claude/rules/*.md" -o -path "*/.claude/skills/*/SKILL.md"); do
  tokens=$(($(wc -c < "$f") / 4))
  echo "$tokens tokens - $f"
done | sort -rn
```

## Size Guidelines

| File Type | Target Lines | Max Lines | Max Tokens |
|-----------|--------------|-----------|------------|
| Root `CLAUDE.md` | 50-70 | 100 | ~800 |
| Child `CLAUDE.md` | 20-40 | 80 | ~600 |
| `.claude/rules/*.md` | 25-50 | 80 | ~600 |
| `.claude/skills/*/SKILL.md` | 40-60 | 100 | ~800 |
| Reference docs | No limit | - | - |

*Token estimates assume ~8 tokens/line for typical markdown.*

## Audit Checklist

### CLAUDE.md Files

- [ ] **Concise** - Under 80 lines (root can be 100)
- [ ] **No verbose explanations** - Cut anything Claude can infer
- [ ] **Commands included** - Things Claude can't guess
- [ ] **Constraints documented** - What prevents bugs/crashes
- [ ] **Plain paths for large docs** - No `@` imports for 100+ line files
- [ ] **No duplication** - Repeated rules belong in `.claude/rules/`

### Rules (.claude/rules/*.md)

- [ ] **Focused** - One concern per file
- [ ] **Has frontmatter** - `paths:` if directory-scoped
- [ ] **Actionable** - Rules prevent mistakes, not explain code
- [ ] **No stale content** - References exist, numbers accurate

### Skills (.claude/skills/*/SKILL.md)

- [ ] **Has frontmatter** - `name:`, `description:`, optional `argument-hint:`
- [ ] **Clear steps** - Numbered or bulleted actions
- [ ] **Portable** - No hardcoded paths or project-specific data
- [ ] **Has checklist** - Completion criteria

## Common Issues

| Issue | Problem | Fix |
|-------|---------|-----|
| `@` importing large docs | Floods context | Use plain paths |
| Stale file references | Confusion, errors | Update or remove |
| Duplicated rules | Maintenance burden | Move to `.claude/rules/` |
| Verbose explanations | Wastes tokens | Cut to constraints only |
| Missing frontmatter | Skills won't load | Add `name:` and `description:` |
| Hardcoded paths | Not portable | Use relative paths or patterns |

## Key Principle

> "For each line, ask: Would removing this cause Claude to make mistakes? If not, cut it."

## Report Format

Output a table per category with columns: File, Lines, Tokens, Status (OK/WARN/FIX). End with Issues Found list and Summary counts.

## References

- Claude Code memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Claude Platform docs: https://platform.claude.com/docs
- Agent skills patterns: https://agentskills.io/home
