---
trigger: always_on
---

1. Code files including tests should have less than 200 lines (if they have more should be refactorized via SRP, abstraction/composition).
2. Use the following test to check modified files follow architecture rules:
   - apps\commonlib> poetry run pytest .\test\architecture_test.py
   - apps\web> npx vitest run src\test\architecture.test.ts
3. Monorepo module's:
   - This project contains several modules in apps folder.
   - Each module use a package manager, check test.* or install.* in scripts folder to know wich to use.
      - for npm tests use `npx vitest run`.
      - always implement parameterized tests when applies.
   - Always run module full suite tests after any change in code.

## Best practices

- Use simpliest SOLID implementation possible.
- Follow repository pattern in data layer.
- Use dependency injection.
- Separate business logic, apis, and repositories.
- Use services for business logic.
- Use repositories for data access logic.
- Use models/entities for data representation.
- Use DTOs for data transfer between layers.
- Follow clean architecture principles.
- Ensure high cohesion and low coupling between components.
- Write unit tests for all layers.
- Use interfaces to define contracts between layers.
- Follow single responsibility principle for classes and methods.
- Use in context simple and meaningful generic names for classes, methods, and variables.
- Avoid code duplication by reusing components and methods (DRY).
- Document architecture decisions and patterns used in the project.
- Ensure scalability and maintainability of the architecture.