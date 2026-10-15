# SonarQube Quality Gate (mandatory before git push)

Before pushing, the local SonarQube scan must succeed and `.sonar-gate-passed`
must match the current `HEAD` and the current `git status --porcelain` hash.

Use:
- Linux/macOS: `scripts/sonar.sh up`, then `scripts/sonar.sh scan`
- Windows: `scripts/sonar.bat up`, then `scripts/sonar.bat scan`

The hooks/plugins block `git push` until the gate passes. Apply minimal, direct fixes
for the reported issues and re-run the scan. Do not add bypass variables unless the
user explicitly authorizes an emergency bypass.