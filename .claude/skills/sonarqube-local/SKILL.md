# SonarQube Local Static Analysis for ASDLC

This is the mandatory quality gate before any push.

## Workflow
1. Run native fast checks (`scripts/test.sh` or `.bat`).
2. Run `scripts/sonar.sh scan` on Linux/macOS or `scripts/sonar.bat scan` on Windows.
3. If SonarQube reports issues, open the local dashboard at `http://localhost:9000`, fix them, and re-scan.
4. Run `scripts/sonar.sh scan` once again until the Quality Gate is OK.
5. Push only after the scan succeeds and `.sonar-gate-passed` matches the current HEAD and working tree.

## Common tools
- Start server: `scripts/sonar.sh up` / `scripts/sonar.bat up`
- Stop server: `scripts/sonar.sh down` / `scripts/sonar.bat down`
- Marker: `.sonar-gate-passed`

## Rules
- Do not add `SKIP_SONAR=1` unless the user explicitly requests an emergency bypass.
- Do not suppress findings unless required by generated code or by explicit project policy.
- Fix the underlying defect instead of changing the rule.