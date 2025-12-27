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

1. Achieve 100% compliance with EU AI Act for high-risk AI systems
2. Implement all required compliance measures (Articles 9-15)
3. Add transparency and human oversight mechanisms
4. Establish risk management and data governance procedures
5. Create comprehensive technical documentation
6. Implement logging and audit trails
7. Prepare for conformity assessment
8. Ensure system can be legally deployed in EU

## Overview

The project is organized into 6 epics (parent tasks) for EU AI Act compliance migration and security hardening:

1. **Epic 1: Immediate Actions (Week 1-2)** - Add AI transparency notices to UI, Implement basic logging for AI operations, Document system architecture and AI components, Create initial risk assessment document
2. **Epic 2: Core Compliance (Month 1)** - Implement risk management system, Enhance data governance (validation, quality checks), Add human oversight mechanisms (review, override, explanations), Complete technical documentation
3. **Epic 3: Advanced Compliance (Month 2-3)** - Implement comprehensive logging and audit trails, Add accuracy monitoring and metrics, Enhance cybersecurity measures, Implement robustness testing and fallback mechanisms
4. **Epic 4: Conformity Assessment (Month 3-4)** - Gather all required documentation, Complete self-assessment, Prepare for third-party assessment if needed, Register system in EU database (if required)
5. **Epic 5: Supporting Tasks** - GDPR alignment, comprehensive testing, documentation, training, and ongoing compliance monitoring
6. **Epic 6: Security Hardening** - Fix critical SQL injection vulnerabilities, Remove hardcoded credentials, Implement authentication/authorization, Restrict CORS, Enhance input validation, Secure error handling, Implement rate limiting

## Technology

1. Python logging framework for structured logging (JSON format)
2. Log aggregation (ELK stack or similar) and monitoring dashboards
3. Markdown documentation with API documentation tools and technical specification templates
4. Version control (Git)
5. Data validation libraries (Pydantic, Cerberus) for data quality checks
6. Data profiling tools
7. React components for transparency notices, explanation interfaces, and human review interfaces
8. Unit tests, integration tests, and compliance validation tests
9. Access control mechanisms, encryption for sensitive data, and secure API endpoints

## Outcome

1. Compliance Metrics: 100% of required AI Act articles implemented, All compliance checklist items completed, Technical documentation complete and up-to-date, Risk management system operational
2. Functional Metrics: All AI operations logged and auditable, Transparency notices visible to all users, Human oversight mechanisms functional, Data governance procedures documented and followed
3. Quality Metrics: Zero critical compliance gaps, All code violations resolved, Documentation reviewed and approved, Conformity assessment passed
4. Operational Metrics: Incident response procedures tested, Monitoring and alerting functional, Regular compliance reviews scheduled, Audit trails maintained for required retention period

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

## Project Backlog

See [Project Backlog](backlog/migration.md) for detailed task breakdown and individual task files.

## Unplanned Tasks Example

Create tasks in /backlog dir, but prefix these tasks with letter "u" - for example "u-task-1.md". Remamber to fallow the same structure inside the task and reference correctly if there is some corelation or dependencies between tasks.

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

    2.1. Commit changes using the commit-standard.md .

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
@commit-standard.md

## Human Notes

## Unplanned tasks standard
 standard (This is to start measuring what was 'overvibed', it would require some standards)
