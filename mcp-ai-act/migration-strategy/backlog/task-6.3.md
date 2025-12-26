# Task ID: 6.3
# Title: Remove Hardcoded Credentials
# Status: [ ] Pending
# Priority: critical
# Owner: DevOps/Backend Team
# Estimated Effort: 8h

## Description
Remove all hardcoded database credentials from the codebase and move them to environment variables or secrets management. This includes credentials in `mysqlUtil.py`, `docker-compose.yml`, and any other configuration files. Use different credentials for dev/staging/production environments.

## Dependencies
- [ ] Task ID: 6.0

## Testing Instructions
1. Verify no credentials in source code
2. Verify environment variables are used
3. Test with different environments (dev/staging/prod)
4. Verify secrets management works
5. Test application connects successfully
6. Verify credentials are not in git history

## Security Review
- Critical security vulnerability - credentials exposed in code
- Verify no credentials in version control
- Ensure secrets management is secure
- Test credential rotation

## Risk Assessment
- **CRITICAL**: Credentials exposed in source code
- If code is leaked, database is immediately accessible
- Same credentials used across all environments
- Can lead to unauthorized access and data breaches

## Acceptance Criteria
- [ ] All hardcoded credentials removed from code
- [ ] Environment variables used for all credentials
- [ ] Different credentials for each environment
- [ ] Secrets management implemented
- [ ] `.env` files in `.gitignore`
- [ ] No credentials in git history (if possible)

## Definition of Done
- [ ] mysqlUtil.py updated to use environment variables
- [ ] docker-compose.yml updated to use environment variables
- [ ] .env.example created (without real credentials)
- [ ] .env added to .gitignore
- [ ] Documentation updated with setup instructions
- [ ] All environments configured
- [ ] Tests written and passing
- [ ] Security audit passed
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: No credentials in code, environment variables used, secrets management working
- **Observable Outcomes**: Application connects, credentials secure, different per environment
- **Quality Attributes**: Secure credential management, no exposed secrets
- **Completion Indicators**: Code updated, env vars configured, audit passed

## Notes
Consider using Docker secrets, AWS Secrets Manager, or HashiCorp Vault for production. For development, `.env` files are acceptable if properly gitignored.

## Strengths
Eliminates credential exposure. Enables proper secret management. Essential for production security.

## Sub-tasks
- [ ] Identify all hardcoded credentials
- [ ] Update mysqlUtil.py to use env vars
- [ ] Update docker-compose.yml to use env vars
- [ ] Create .env.example file
- [ ] Update .gitignore
- [ ] Update documentation
- [ ] Configure dev/staging/prod environments
- [ ] Test credential loading
- [ ] Security audit

## Completed
[ ] Pending / [x] Completed

