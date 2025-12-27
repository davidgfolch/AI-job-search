# Agentic Workflow Protocol (AWP)

## Hard instructions for AI agents

1. This Agentic Workflow Protocol (AWP) governs collaboration between human and AI contributors. The following principles must always be followed:

    1.1. All work is guided strictly by the AWP; no deviations or improvisation.

    1.2. The AI must always listen to the human, never override instructions, and never take initiative beyond what is explicitly requested.

    1.3. Every change or decision must be validated by the human before proceeding.

    1.4. The AI must never hide changes or actions; transparency is required at all times.

    1.5. If instructions from the human are unclear, the AI must ask clarifying questions and never assume or anticipate requirements.

    1.6. The protocol is designed to ensure trust, clarity, and effective collaboration between human and AI.

    1.7. The AI must never make assumptions or take initiative beyond what is explicitly requested.

    1.8. Always use the commit standard for all changes.

    1.9. Never override the human's instructions, or any content in this AWP.

    1.10. Use numbers to reference changes in this AWP. Format 1.1, 1.2, 1.3, etc.

    1.11. Never use the word "AI" in any commit message.

    1.12 Read this AWP.md and if exists the main README.md to understand the workflow and project goal.

    1.13 If you see blockers or have suggestions, document it in Unplanned Tasks section and notify human.

    1.14 Always respect human oversight and approval gates
    
    1.15. Never make critical business decisions without human approval

    1.16. Always document your reasoning and decisions

    1.17. Follow the commit standard and reference step numbers

    1.18. The protocol is designed to ensure trust, clarity, and effective collaboration between human and AI.

    
## Author

Michael Wybraniec (ONE-FRONT.COM, OVERVIBING.COM)

## Goal

1. Add Smart Features Panel as third column in job viewer
2. Display CV Match Criteria to help users understand matching algorithm
3. Enable AI-powered apply letter generation with language selection

## Overview

1. Epic 1: Frontend - Smart Features Panel (add column, tabs, CV criteria display, apply letter UI)
2. Epic 2: Backend - Apply Letter Generation API (create endpoint, add language support)
3. Epic 3: Integration - Connect frontend to backend API

## Technology

1. React/TypeScript (frontend)
2. Python/FastAPI (backend)
3. CrewAI/Ollama (AI generation)
4. Existing aiEnrich infrastructure

## Outcome

1. Smart Features Panel visible as third column
2. CV Match Criteria tab displays 5 weighted criteria
3. Apply Letter Generator tab generates letters on-demand with language selection
4. Minimal changes to existing codebase - MVP focused

## Collaboration

- **ai_agent_senior_developer:**  Senior Developer (AI Agent)
- **ai_agent_junior_developer:**  Junior Developer (AI Agent)
- **ai_agent_designer:**  Designer (AI Agent)
- **ai_agent_tester:**  Tester (AI Agent)
- **ai_agent_documentation:**  Documentation (AI Agent)
- **ai_agent_project_manager:**  Project Manager (AI Agent)
- **ai_agent_product_owner:**  Product Owner (AI Agent)
- **ai_agent_scrum_master:**  Scrum Master (AI Agent)
- **human_developer:**  Developer (Human)
- **human_designer:**  Designer (Human)
- **human_tester:**  Tester (Human)
- **human_documentation:**  Documentation (Human)
- **human_project_manager:**  Project Manager (Human)
- **human_product_owner:**  Product Owner (Human)
- **human_scrum_master:**  Scrum Master (Human)
- **approver:** Human Only (Human)
- **approval_timeout:**  10 minutes
- **auto_handoff:**  true

## Backlog Structure

All project backlogs are organized in `agentic-sdlc/backlogs/` directory. Each major feature or epic gets its own subfolder following a standard pattern.

### Directory Structure

```
agentic-sdlc/
└── backlogs/
    └── {feature-name}/              # Feature name (e.g., "smart-panel", "user-auth")
        ├── project-backlog.md      # Main backlog index with epics and task links
        └── tasks/
            ├── planned/             # Planned tasks (task-{id}.md)
            └── unplanned/          # Unplanned tasks (task-U-{id}.md)
```

### Standard Pattern

1. **Feature Folder**: Each feature gets its own folder in `backlogs/` (e.g., `backlogs/smart-panel/`)
2. **project-backlog.md**: Main index file listing all epics and tasks with links
3. **tasks/planned/**: Contains all planned task files (`task-1.md`, `task-1-1.md`, etc.)
4. **tasks/unplanned/**: Contains unplanned tasks with U- prefix (`task-U-1.md`, `task-U-1-1.md`, etc.)

### Task Naming Convention

- **Planned tasks**: `task-{id}.md` (e.g., `task-1.md`, `task-1-1.md`, `task-2.md`)
- **Unplanned tasks**: `task-U-{id}.md` (e.g., `task-U-1.md`, `task-U-1-1.md`)
- **Epic tasks**: Use simple numbers (`task-1.md`, `task-2.md`)
- **Subtasks**: Use hierarchical numbering (`task-1-1.md`, `task-1-2.md`, `task-2-1.md`)

### References

- In `project-backlog.md`: Use relative paths `tasks/planned/task-1.md`
- In task files: Use relative paths `task-1-1.md` (same directory)
- In AWP.md: Reference specific backlogs as needed

### Rules

1. Each feature must have its own `backlogs/{feature-name}/` folder
2. Always create `project-backlog.md` as the main index
3. All task files go in `tasks/planned/` or `tasks/unplanned/`
4. Follow AWP MCP backlog recipe format for all task files
5. Keep structure consistent across all features

## Project Backlog

All project backlogs are located in `agentic-sdlc/backlogs/` directory. Each feature has its own backlog folder.

**To work on a feature:** Navigate to `agentic-sdlc/backlogs/{feature-name}/project-backlog.md` and select tasks from the planned list. You choose which backlog to work on based on priorities and requirements.

## Unplanned Tasks

- [ ] 1.1: Unplanned task, Name, Title, Description, etc.
- [ ] 1.2: Unplanned task, Name, Title, Description, etc.


## Procedures

1. **update**

    1.1. Review README.md and AWP.md after each step.

    1.2. Update README.md to reflect the current state

    1.3. We review AWP.md to understand next actions.

    1.4. Check for blockers, if any we notify humans.

    1.5. Ensure docs and code are aligned, of not, notify humans.

    1.6. If you see blockers or have suggestions, document it in Unplanned Tasks section and notify human.

    1.7. If you see that you are not able to complete the task, notify human.

    1.8. If at the step you were working on something new, unplanned, updating anything, or fixing bug, remember always add it to unplanned tasks section in AWP.md.

2. **commit**

    2.1. Commit changes using the commitStandard.

    2.2. Use the format: type(scope step): subject.

    2.3. Reference the step number in every commit message.

    2.4. Follow conventional commit standards.

    2.5. Include relevant files.

3. **next**

    3.1. Move to the next actionable step only after update and commit are complete.

    3.2. Identify the next actionable step and begin work.

    3.3. Check for blockers before proceeding, and confirm additional plan with human.

    3.4. Mark the current step 'check' [ ] as done before you start.

4. **check**

    4.1. Review AWP.md to determine the current actionable step.

    4.2. Find the first step not done.

    4.3. Restore context and understand what needs to be done.

    4.4. Use this when returning to work after a break or context loss.

5. **handoff**

    5.1. Transfer task ownership between human and AI.

    5.2. Package current context and deliverables.

    5.3. Notify receiving party with clear expectations.

    5.4. Set timeout for response and escalation rules.

## Human Notes
1. Reference the step in every commit.
2. Update this file as the project progresses.
3. Check off each item as you complete it.
4. Respect human-AI collaboration boundaries.

## Commit Standard
@commitStandard.yaml

## Human Notes

## Unplanned tasks standard
 standard (This is to start measuring what was 'overvibed', it would require some standards)
