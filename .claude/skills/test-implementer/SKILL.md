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
- **Parameterized Tests**: Use `@pytest.mark.parametrize` (Python) or `test.each` (Vitest) to avoid duplicate test code when testing the same function with multiple inputs/outputs. Each case must have a descriptive `id=` or name.
- **Performance**: Unit tests MUST execute quickly (under 500ms each).
- **Mocking**: To achieve the performance goal, all external layers (database, network, file system, etc.) and dependencies MUST be properly mocked. Do not rely on real I/O operations in unit tests.
- **Handling State Updates (`act`)**: Always wrap code that triggers React state updates in `act(...)`.
    - Use `await waitFor(() => { ... })` for asynchronous updates in standard tests.
    - **Fake Timers**: When using `vi.useFakeTimers()`, use `await act(async () => await vi.advanceTimersByTimeAsync(MS))` to advance time and flush microtasks. Avoid `waitFor` with fake timers unless time is advanced manually.
    - **Initial Check on Mount**: If a hook/component performs async work on mount, use `await vi.advanceTimersByTimeAsync(0)` (with fake timers) or `await waitFor(...)` (with real timers) to ensure it completes before asserting or clearing mocks.
- **TanStack Query (React Query)**: Ensure ALL query functions used by the SUT are mocked. If using `vi.mock()`, explicitly mock setiap function with `mockResolvedValue` to avoid "Query data cannot be undefined" errors, as React Query v5+ does not allow `undefined` returns.

## 4. Running Tests
Always use the centralized test script to run tests. Never run `poetry run pytest`, `uv run pytest`, or `npx vitest run` directly. Always include `commonlib` (it contains architecture tests and is a shared library) plus any other modified `apps/*` modules.
```bash
# Run tests for commonlib + specific apps (Linux/Mac)
./scripts/test.sh commonlib scrapper
# Run tests for commonlib + specific apps (Windows)
.\scripts\test.bat commonlib scrapper

# Run all tests (Linux/Mac)
./scripts/test.sh

# Run all tests with coverage
./scripts/test.sh --coverage
```

## 5. Architecture Verification
Refuse to complete the task without verifying architecture compliance. Architecture tests are included when running the centralized test script for `commonlib`.

## Usage
- When creating a new unit test for `MyService`:
    1. Create `test/MyService_test.py` (or `.test.ts`).
    2. Instantiate `sut = MyService()`.
    3. Run tests via `./scripts/test.sh commonlib <app>` (or `.bat` on Windows).
    4. Architecture rules are enforced by `architecture_test.py` in commonlib's test suite.
