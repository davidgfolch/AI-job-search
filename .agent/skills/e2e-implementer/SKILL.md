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
-   **Page Object Model**: ALWAYS use POM. Do not define selectors or logic inside specs.
-   **Independence**: Tests should not depend on each other.
-   **Selectors**: Use user-facing locators (e.g., `getByRole`, `getByText`) over CSS selectors where possible.
-   **Database**: Do NOT use the production database. Use the `scripts/run_e2e_tests.py` script which handles isolation.

## 4. Architecture Verification
-   Ensure `apps/e2e` does not import internal implementations from other apps directly (unless it's a shared type/constant). It should interact via the browser.
- Run commonlib/.../architecture_test.py to verify the architecture.

## Usage
-   **Preferred Method**: Run `python scripts/run_e2e_tests.py` from the root. This will:
    1. Setup a temporary isolation database.
    2. Start the backend on a free port.
    3. Run the tests.
-   Manual run: `npm test` inside `apps/e2e` (WARNING: Configured against local dev environment by default).
