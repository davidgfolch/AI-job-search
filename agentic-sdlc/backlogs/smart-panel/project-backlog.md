# Smart Features Panel - Project Backlog

## Planned Tasks

### Feature: Smart Features Panel (MVP)
Add a third column/panel that opens next to the job detail view. This panel contains tabs for:
1. CV Match Criteria - Display the 5 weighted criteria used for matching
2. Apply Letter Generator - Generate personalized apply letters using AI (max 2000 words, language selection, on-demand generation)

## Epics

### Epic 1: Frontend - Smart Features Panel
- [ ] [Task 1: Epic 1 - Frontend Smart Features Panel](tasks/planned/task-1.md) (8.5h)
  - [ ] [Task 1.1: Add Smart Features Panel Column](tasks/planned/task-1-1.md) (3h)
  - [ ] [Task 1.2: Add Tabs to Smart Features Panel](tasks/planned/task-1-2.md) (1.5h)
  - [ ] [Task 1.3: Implement CV Match Criteria Display Tab](tasks/planned/task-1-3.md) (1h)
  - [ ] [Task 1.4: Implement Apply Letter Generator Tab UI](tasks/planned/task-1-4.md) (3h)

### Epic 2: Backend - Apply Letter Generation API
- [ ] [Task 2: Epic 2 - Backend Apply Letter Generation](tasks/planned/task-2.md) (5h)
  - [ ] [Task 2.1: Create Backend API for Apply Letter Generation](tasks/planned/task-2-1.md) (4h)
  - [ ] [Task 2.2: Add Language Selection for Apply Letter](tasks/planned/task-2-2.md) (1h)

### Epic 3: Integration - Connect Frontend to Backend
- [ ] [Task 3: Epic 3 - Integration](tasks/planned/task-3.md) (2h)
  - [ ] [Task 3.1: Integrate Apply Letter Generator with Frontend](tasks/planned/task-3-1.md) (2h)

**Total Estimated Effort: ~15.5 hours**

## Unplanned Tasks

*No unplanned tasks yet*

## Completed Tasks

*No completed tasks yet*

---

**Project Goals:** Add Smart Features Panel as third column in job viewer, Display CV Match Criteria to help users understand matching algorithm, Enable AI-powered apply letter generation with language selection
**Technology Stack:** React/TypeScript (frontend), Python/FastAPI (backend), CrewAI/Ollama (AI generation), Existing aiEnrich infrastructure
**Success Criteria:** Smart Features Panel visible as third column, CV Match Criteria tab displays 5 weighted criteria, Apply Letter Generator tab generates letters on-demand with language selection, Minimal changes to existing codebase - MVP focused

## Notes
- **MVP Focus**: All tasks are simplified for MVP - no overkill, minimal changes
- **Layout**: Just add a third column "Smart Features Panel" next to viewer-right
- **Minimal Changes**: Reuse existing patterns, styles, and infrastructure
- **Scope**: Simple tabs, basic UI, functional backend - can enhance later
- **AWP Compliance**: This backlog follows Agentic Workflow Protocol (AWP) standards from AWP.md
- **Task Structure**: Epics (1, 2, 3) contain detailed subtasks (1.1, 1.2, etc.)
