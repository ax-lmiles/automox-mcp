# Documentation Reference

Portable patterns for CLAUDE.md and project documentation.

## Official Documentation

- Memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Platform: https://platform.claude.com/docs
- Agent skills: https://agentskills.io/home

## docs/ Folder Structure

Organize by purpose, not file type:

```
docs/
├── README.md                 # Index with folder descriptions
├── architecture/             # System design, decisions
│   ├── api.md
│   ├── database.md
│   └── decisions/            # ADRs (Architecture Decision Records)
├── guides/                   # How-to instructions
│   ├── getting-started.md
│   ├── deployment.md
│   └── troubleshooting.md
├── reference/                # Large reference material (read on-demand)
│   ├── api-spec.md
│   └── style-guide.md
└── specifications/           # Output/feature requirements
    ├── feature-a/
    │   ├── README.md
    │   └── requirements.md
    └── feature-b/
```

### Folder Naming Conventions

| Pattern | Use For | Examples |
|---------|---------|----------|
| `kebab-case/` | Multi-word folders | `getting-started/`, `api-reference/` |
| Singular nouns | Category folders | `guide/`, `reference/`, `spec/` |
| Plural nouns | Collection folders | `decisions/`, `examples/` |

### File Naming Conventions

| Pattern | Use For | Examples |
|---------|---------|----------|
| `README.md` | Folder index/overview | Every folder should have one |
| `UPPERCASE.md` | Important project files | `CLAUDE.md`, `CONTRIBUTING.md` |
| `kebab-case.md` | Regular docs | `getting-started.md`, `api-patterns.md` |
| `NN-name.md` | Sequential content | `01-intro.md`, `02-setup.md` |

**Key principle:** Reference docs are large (100+ lines). Never @ import them - use plain paths so Claude reads on-demand.

**Sizing guideline:** Consider splitting docs over 600 lines into focused files, unless the document is:
- A comprehensive guide meant to be read end-to-end (e.g., testing guide)
- A unified reference (e.g., database schema, API spec)
- A roadmap or timeline that benefits from single-file view

## Loading Behavior

| Content | When Loaded |
|---------|-------------|
| Root `CLAUDE.md` | Session start |
| `.claude/rules/*.md` with `paths:` | When working in matching paths |
| Child `CLAUDE.md` files | When Claude reads files in that directory |
| `@` imported files | Immediately when parent loads |
| Plain path references | On-demand when Claude needs them |

## Sizing Guidelines

| File Type | Target | Guideline |
|-----------|--------|-----------|
| Root CLAUDE.md | 50-70 lines | Keep concise, link to details |
| Child CLAUDE.md | 20-40 lines | Can exceed for complex modules |
| Path-scoped rules | 25-50 lines | Focused on specific concerns |
| Reference docs | No limit | Read on-demand via plain paths |

**These are guidelines, not hard rules.** The key principle is:

> "Would removing this cause Claude to make mistakes? If not, cut it."

**When to exceed guidelines:**
- Complex modules with many gotchas (e.g., database patterns, deployment configs)
- Active development where patterns are still being established
- Critical workflows where mistakes are costly

**When to stay concise:**
- Stable, well-understood code
- Standard patterns Claude can infer
- Reference material that belongs in docs/ instead

## CLAUDE.md Sections

1. **Title and Overview** - 1-2 sentences max
2. **Reference Docs** - Plain paths to large docs
3. **Critical Rules** - Only what prevents mistakes
4. **Commands** - What Claude can't guess

## Cross-Referencing

```markdown
# Small CLAUDE.md (< 50 lines) - @ is OK
@src/lib/auth/CLAUDE.md

# Large reference doc - plain path
docs/reference/api-spec.md
```

## When to Create CLAUDE.md

**Create when:**
- Module has non-obvious constraints
- Technical gotchas cause bugs
- Commands Claude can't guess

**Skip when:**
- Standard patterns
- Self-explanatory code
- Parent CLAUDE.md covers it

## Documentation Checklist

- [ ] Content prevents mistakes (not just reference material)
- [ ] No @ imports to large docs (100+ lines)
- [ ] Sized appropriately for module complexity
- [ ] docs/ organized by purpose
- [ ] Consistent naming conventions
- [ ] README.md in each docs/ subfolder

## README.md vs CLAUDE.md

| Aspect | README.md | CLAUDE.md |
|--------|-----------|-----------|
| Audience | Humans | Claude/AI |
| Content | Explanations, context | Constraints, gotchas |
| Length | Any length | As needed for complexity |
| Purpose | Understanding | Preventing mistakes |
| Examples | Detailed tutorials | Brief patterns |

**Rule of thumb:** If it helps understanding → README. If it prevents bugs → CLAUDE.md.

## Documentation Patterns

**Troubleshooting:** Use `Symptom → Cause → Solution` format.

**Deprecation:** Include migration steps and removal timeline.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| @ importing large docs | Floods context | Use plain paths |
| Duplicating rules | Maintenance burden | Use `.claude/rules/` |
| Documenting obvious code | Wastes context | Delete it |
| No README in docs/ folders | Hard to navigate | Add folder index |
| Mixing human/AI docs | Confusing | Separate README/CLAUDE.md |

## Adapting to New Projects

1. Read existing CLAUDE.md files for conventions
2. Audit docs/ structure - reorganize by purpose if needed
3. Check for repeated rules → move to `.claude/rules/`
4. Audit @ imports → convert large docs to plain paths
5. Add README.md to docs/ subfolders lacking them
6. Separate README.md (human) from CLAUDE.md (AI)
