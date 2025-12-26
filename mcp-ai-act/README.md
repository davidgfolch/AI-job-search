# MCP AI Act Compliance

This directory contains EU AI Act compliance assessment results, migration strategy, and related documentation for the AI Job Search project refactoring.

## Overview

The AI Job Search system has been assessed as a **HIGH-RISK AI SYSTEM** under the EU AI Act (Regulation (EU) 2021/0106) because it:

- Automates CV matching using AI agents (CrewAI)
- Influences employment decisions through compatibility scoring
- Processes personal employment data
- Makes AI-powered recommendations for job applications

## Contents

### 📊 `report-20250127_220430.md`

Comprehensive compliance assessment report showing:

- Current compliance status (33% compliant)
- Risk classification and applicable AI Act articles
- Detailed gap analysis and recommendations
- System components analyzed

### 📋 `migration-strategy/`

Contains the migration plan to achieve 100% EU AI Act compliance:

- **`awp-readme.md`** - Agentic Workflow Protocol (AWP) for managing the compliance migration
- **`backlog/`** - Detailed task breakdown organized into 6 epics:
  - Epic 1: Immediate Actions (Week 1-2)
  - Epic 2: Core Compliance (Month 1)
  - Epic 3: Advanced Compliance (Month 2-3)
  - Epic 4: Conformity Assessment (Month 3-4)
  - Epic 5: Supporting Tasks
  - Epic 6: Security Hardening
- **`commit-standard.md`** - Commit message standards for the migration

### 📁 `session-*/`

Historical session data from compliance assessment runs.

## Goal

Achieve 100% compliance with EU AI Act requirements for high-risk AI systems, including:

- Risk management system implementation
- Data governance and quality management
- Technical documentation
- Record keeping and audit trails
- Transparency and user information
- Human oversight mechanisms
- Accuracy, robustness, and cybersecurity measures

## Status

🔴 **NON-COMPLIANT** - Migration in progress

See `migration-strategy/awp-readme.md` for current progress and next steps.

## Contact

Michael Wybraniec (ONE-FRONT.COM, AI ENGINEERING BARCELONA)
