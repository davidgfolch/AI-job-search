# AI Job Search Default Development Guide

This guide covers setting up your development environment, running the application manually, and testing.

## Development with VS Code

To ensure VS Code automatically selects the correct interpreter for each project:

1. **Open the Workspace**: Open the `AI-job-search.code-workspace` file in VS Code (`File > Open Workspace from File...`).
2. **Interpreter Selection**: The workspace is configured to automatically pick up the `.venv` in each application folder (`apps/backend`, `apps/scrapper`, etc.).

> **Note the root `pyproject.toml` is not required** for deploying or running the applications**, as each module (in `apps/`) has its own dependencies and configuration for Docker and CI/CD. However, it is **highly necessary for the local Developer Experience (DX)**. It configures the virtual environment used by the VS Code Workspace (`.venv`), providing global linting/formatting tools (like `black`, `ruff`, and `mypy`), and ensures the IDE can correctly resolve cross-module imports like `commonlib`.



## Testing

Run all tests across the monorepo:

- **Linux**: `./scripts/test.sh` (Optional: `--coverage`)
- **Windows**: `.\scripts\test.bat` (Optional: `--coverage`)

Run specific app tests (single or multiple):

- **Linux**: `./scripts/test.sh commonlib` or `./scripts/test.sh commonlib web e2e`
- **Windows**: `.\scripts\test.bat commonlib` or `.\scripts\test.bat commonlib web e2e`

## Agentic SDLC

Agent skills, rules, and workflows (including graphify and the dependabot agent) are documented in [AGENTIC_SDLC.md](AGENTIC_SDLC.md). All agent skills live under `.claude/skills/`.

## Related Documentation

- **Agentic SDLC**: [AGENTIC_SDLC.md](AGENTIC_SDLC.md)
- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
