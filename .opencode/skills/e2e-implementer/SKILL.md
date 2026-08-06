---
name: e2e-implementer
description: Create and run E2E tests using Playwright in the `apps/e2e` module.
---
# E2E Implementer Instructions

Use this skill when implementing or modifying End-to-End (E2E) tests. These tests are distinct from unit/integration tests and are housed in a dedicated module.

## 1. Location & Structure
-   **Module**: All E2E tests MUST be located in `apps/e2e`.
-   **Structure**:
    -   `specs/`: Contains test files (`*.spec.ts`).
    -   `pages/`: Page Object Models (POM).
    -   `utils/`: Helper functions.

## 2. Naming Conventions
-   **Test Files**: Must end in `.spec.ts` (Playwright standard).
-   **Page Objects**: Must end in `Page.ts` (e.g., `LoginPage.ts`).

## 3. Best Practices
- **Page Object Model**: ALWAYS use POM. Do not define selectors or logic inside specs.
- **Independence**: Tests should not depend on each other.
- **Selectors**: ALWAYS use IDs to locate DOM objects. Ensure target elements have unique `id` attributes in the source code. Avoid using text-based locators or CSS classes unless absolutely necessary.
-   **Database**: Do NOT use the production database. All API interactions are mocked at the browser level via `page.route()` (see `specs/common.helpers.ts` and per-spec helpers). No backend or database is required.
-   **Coverage**: Specs MUST import `test`/`expect` from `./coverage.fixtures` (not `@playwright/test`) so Chromium V8 coverage is fed to monocart. New spec files must follow this import pattern; otherwise frontend coverage silently drops.

## 4. Architecture Verification
-   Ensure `apps/e2e` does not import internal implementations from other apps directly (unless it's a shared type/constant). It should interact via the browser.
- Run commonlib/.../architecture_test.py to verify the architecture.

## Usage
-   **Preferred Method**: Run `npm test` inside `apps/e2e`. Playwright starts its own Vite dev server for `apps/web` on port 5174 and mocks all `/api/**` requests via `page.route()` — no backend, database, or Docker services required.
-   **Subset**: `npm test -- --grep "pattern"` (optionally `--project=chromium`).
-   **New endpoints**: If the safety net logs `UNMOCKED API REQUEST`, add a mock for that endpoint in the relevant helper (registered after the safety net).
