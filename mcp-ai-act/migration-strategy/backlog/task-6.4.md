# Task ID: 6.4
# Title: Restrict CORS Origins
# Status: [ ] Pending
# Priority: high
# Owner: Backend Team
# Estimated Effort: 4h

## Description
Restrict CORS to specific allowed origins instead of allowing all origins (`allow_origins=["*"]`). Configure different origins for development and production environments. Remove `allow_credentials=True` if not needed, and restrict methods and headers to only what's necessary.

## Dependencies
- [ ] Task ID: 6.0

## Testing Instructions
1. Test with allowed origins (should work)
2. Test with disallowed origins (should be blocked)
3. Test in development environment
4. Test in production environment
5. Verify CORS headers are correct
6. Test preflight requests

## Security Review
- High-severity vulnerability - allows all origins
- Verify only allowed origins can access API
- Test CSRF protection
- Verify credentials handling

## Risk Assessment
- **HIGH**: Any website can make requests to API
- Enables CSRF attacks
- Allows unauthorized access from malicious sites
- Can lead to data exfiltration

## Acceptance Criteria
- [ ] CORS restricted to specific origins
- [ ] Different origins for dev/prod
- [ ] Methods restricted to necessary ones
- [ ] Headers restricted to necessary ones
- [ ] `allow_credentials` removed if not needed
- [ ] CORS tests pass

## Definition of Done
- [ ] main.py CORS configuration updated
- [ ] Environment-specific origins configured
- [ ] Methods restricted
- [ ] Headers restricted
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: CORS restricted, only allowed origins work, tests passing
- **Observable Outcomes**: Unauthorized origins blocked, authorized origins work, CSRF protected
- **Quality Attributes**: Secure CORS configuration, proper origin restrictions
- **Completion Indicators**: Configuration updated, tests passing, audit passed

## Notes
Use environment variables for allowed origins. Example: `allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")`

## Strengths
Prevents unauthorized API access. Protects against CSRF. Essential for production security.

## Sub-tasks
- [ ] Identify required origins (dev/prod)
- [ ] Update CORS configuration in main.py
- [ ] Use environment variables for origins
- [ ] Restrict methods and headers
- [ ] Remove allow_credentials if not needed
- [ ] Write CORS tests
- [ ] Test with different origins
- [ ] Update documentation

## Completed
[ ] Pending / [x] Completed

