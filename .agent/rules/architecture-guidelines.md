---
trigger: always_on
---

1. Code files including tests should have less than 200 lines (if they have more should be refactorized via SRP, abstraction/composition).
2. Use the following test to check modified files follow architecture rules:
   - apps\commonlib> poetry run pytest .\test\architecture_test.py
   - apps\web> npx vitest run src\test\architecture.test.ts
3. Monorepo module's:
   - This project contains several modules in apps folder.
   - Each modulee use a package manager, check scripts/test.bat or test.sh to know wich to use.
      - for npm tests use `npx vitest run`.