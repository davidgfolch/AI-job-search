---
trigger: always_on
---

1. Code files including tests should have less than 200 lines (if they have more should be refactorized via abstraction & composition). Use the following test to check modified files follow those rules:
   - apps\commonlib> clear && poetry run pytest .\test\architecture_test.py
2. Monorepo module's:
   5.1 This project contains several modules (apps & packages).
   5.2 Each modules use a package manager:
   - uv for apps/backend, apps/AiEnrich & apps/AiEnrichNew.
   - poetry for apps/commonlib, apps/viewer and apps/scrapper .
   - npm for apps/web, for tests run `npm test -- run`.