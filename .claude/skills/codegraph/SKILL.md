---
name: codegraph
description: Query and maintain the CodeGraph code-intelligence index that is the project's default way to explore the codebase.
---
# CodeGraph

[CodeGraph](https://github.com/colbymchenry/codegraph) is the project's default code-intelligence / knowledge-graph tool. It indexes the repository into the local, gitignored `.codegraph/` directory and exposes both a CLI and MCP tools (`codegraph_explore`, `codegraph_node`).

`scripts/install.sh` / `scripts/install.bat` install it, wire its MCP server into the detected agents (Claude Code, opencode, Cursor, …) and build the index with `codegraph install --yes --init`. The background daemon watches the repo and auto-syncs changed files, so the graph normally stays fresh on its own.

## When to use it

- Start any codebase question with CodeGraph instead of `grep`/`rg` or source browsing.
- Before editing a symbol, check its callers, callees, blast radius and affected tests.
- Use it to locate entrypoints and subsystems without reading whole files.

## MCP tools vs CLI

When the CodeGraph MCP server is available, prefer its tools:

| Need | MCP tool |
|------|----------|
| Explore an area or question | `codegraph_explore` |
| One symbol, file, or caller/callee trail | `codegraph_node` |

Otherwise use the CLI (same output). Run commands from the repo root; use `-p <path>` to target another checkout.

| Goal | Command |
|------|---------|
| Explore a question / area | `codegraph explore "<question>"` |
| Build task context with code blocks | `codegraph context "<task>"` |
| Search symbols by name | `codegraph query <text>` |
| One symbol's source + caller/callee trail | `codegraph node <symbol>` |
| Read a file with line numbers + dependents | `codegraph node <path>` |
| Callers / callees | `codegraph callers <symbol>` / `codegraph callees <symbol>` |
| Blast radius of a change | `codegraph impact <symbol>` |
| Tests affected by changed files | `codegraph affected <files...>` |
| File structure from the index | `codegraph files` |
| Index status and stats | `codegraph status` |
| Incremental sync (daemon does this automatically) | `codegraph sync` |
| Full rebuild | `codegraph index` |

## Examples

```bash
codegraph explore "how does the scrapper scheduler dispatch platforms"
codegraph node ScrapperScheduler
codegraph callers runSpecifiedScrappers
codegraph impact jobWriteRepository
codegraph affected apps/backend/repositories/jobWriteRepository.py
```

## Rules

- Prefer CodeGraph results over raw file reads; only open a file for the lines the graph or an earlier read already located.
- `.codegraph/` is generated local data: never hand-edit or commit it, and never count it as documentation.
- The daemon keeps the index fresh; if `codegraph status` looks stale, run `codegraph sync`, then `codegraph index` as a last resort.
- `codegraph uninit` removes this project's index; `codegraph uninstall --yes` removes the agent wiring and CLI. Both are handled by `scripts/uninstall.*`.
