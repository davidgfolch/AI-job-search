# AI Job Search Default Development Guide

This guide covers setting up your development environment, running the application manually, and testing.

## Development with VS Code

To ensure VS Code automatically selects the correct interpreter for each project:

1. **Open the Workspace**: Open the `AI-job-search.code-workspace` file in VS Code (`File > Open Workspace from File...`).
2. **Interpreter Selection**: The workspace is configured to automatically pick up the `.venv` in each application folder (`apps/backend`, `apps/scrapper`, etc.).

## Testing

Run all tests across the monorepo:

- **Linux**: `./scripts/test.sh` (Optional: `--coverage`)
- **Windows**: `.\scripts\test.bat` (Optional: `--coverage`)

Run specific app tests (single or multiple):

- **Linux**: `./scripts/test.sh commonlib` or `./scripts/test.sh commonlib web e2e`
- **Windows**: `.\scripts\test.bat commonlib` or `.\scripts\test.bat commonlib web e2e`

## Agent Skills

The agent has access to specialized skills located in `.agent/skills`.

### Skill Builder
A meta-skill used to create new skills for the agent.

**Usage:**
Ask the agent to "create a new skill named [skill-name]" or "use the skill builder".

**Location:** `.agent/skills/skill-builder/SKILL.md`

## Related Documentation

- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
