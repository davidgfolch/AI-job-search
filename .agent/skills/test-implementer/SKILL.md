---
name: test-implementer
description: Implement and run tests adhering to valid architecture and best practices.
---
# Test Implementer Instructions

Use this skill when you need to implement or run tests. Follow these strict guidelines to ensure architectural compliance.

## 1. Test Location & Structure
- **Location**: Test code MUST be placed inside a `test` folder that is a direct child of the SUT (Subject Under Test) production code folder.
    - Example: If code is in `src/feature/my_service.ts`, test MUST be in `src/feature/test/my_service.test.ts`.
- **Micro-architecture**: 
    - Do NOT keep all tests in a single file if it grows too large (>200 lines).
    - Use abstraction to separate concerns:
        - `*_test.py` or `*.test.ts`: The actual test cases.
        - `*_fixtures.py` / `*.fixtures.ts`: Test data setup and fixtures.
        - `*_mocks.py` / `*.mocks.ts`: Mock definitions.
    - **Separation**: Test code must be strictly separated from production code.

## 2. Naming Conventions
- **SUT Instance**: Variable name for the service/class under test instance MUST be `sut`.
- **Test Files**: Must end in `_test.py` (Python) or `.test.ts` (TypeScript).
- **Exceptions**: E2E tests (Playwright) are handled by the `e2e-implementer` skill and live in `apps/e2e`. They use `.spec.ts`.

## 3. Coding Best Practices
- **Abstraction**: Avoid duplicated code. Extract common setup, teardown, and helper logic into specialized test files (see Structure above).
- **Constants**: Reuse production code constants. Do NOT duplicate string literals or magic numbers in tests; import them from the production code.
- **SOLID/KISS**: Keep tests simple and focused.
- **Performance**: Unit tests MUST execute quickly (under 500ms each).
- **Mocking**: To achieve the performance goal, all external layers (database, network, file system, etc.) and dependencies MUST be properly mocked. Do not rely on real I/O operations in unit tests.

## 4. Architecture Verification
Refuse to complete the task without verifying architecture compliance.
- **CommonLib**: Run `poetry run pytest apps/commonlib/commonlib/test/architecture_test.py` (adjust path as needed from CWD).
- **Web**: Run `npx vitest run apps/web/src/test/architecture.test.ts` (adjust path as needed from CWD).

## Usage
- When creating a new unit test for `MyService`:
    1. Create `test/MyService_test.py` (or `.test.ts`).
    2. Instantiate `sut = MyService()`.
    3. Run tests.
    4. Run architecture tests to enforce rules.
