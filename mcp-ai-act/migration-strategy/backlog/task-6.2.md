# Task ID: 6.2
# Title: Fix SQL Injection in mysqlUtil.py String Formatting
# Status: [ ] Pending
# Priority: high
# Owner: Backend Team
# Estimated Effort: 12h

## Description
Refactor SQL queries in `mysqlUtil.py` that use string formatting (`.format()`) to use parameterized queries exclusively. While `avoidInjection()` is called, the string formatting approach is fragile and error-prone. Replace all `.format()` calls with proper parameterized queries.

## Dependencies
- [ ] Task ID: 6.0

## Testing Instructions
1. Test all queries that were refactored
2. Verify SQL injection attempts are prevented
3. Test with various input values
4. Run SQL injection test suite
5. Verify no regressions in functionality

## Security Review
- High-severity vulnerability - string formatting is fragile
- Verify all string formatting removed from SQL
- Ensure parameterized queries used everywhere
- Test for SQL injection vectors

## Risk Assessment
- **HIGH**: String formatting can be bypassed if validation is missed
- Potential for future vulnerabilities
- Current validation may not catch all cases
- Refactoring reduces attack surface

## Acceptance Criteria
- [ ] All `.format()` calls removed from SQL queries
- [ ] Parameterized queries used exclusively
- [ ] All queries tested and working
- [ ] SQL injection tests pass
- [ ] No regressions in functionality

## Definition of Done
- [ ] mysqlUtil.py refactored
- [ ] SELECT_APPLIED_JOB_IDS_BY_COMPANY refactored
- [ ] SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT refactored
- [ ] All string formatting removed
- [ ] Parameterized queries implemented
- [ ] Tests written and passing
- [ ] Security audit passed
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: All formatting removed, parameterized queries used, tests passing
- **Observable Outcomes**: Queries work correctly, SQL injection prevented, no regressions
- **Quality Attributes**: Secure, maintainable SQL query code
- **Completion Indicators**: Code refactored, tests passing, audit passed

## Notes
This affects `SELECT_APPLIED_JOB_IDS_BY_COMPANY` and related queries. Ensure all callers are updated to use parameterized approach.

## Strengths
Eliminates fragile string formatting. Reduces SQL injection risk. Makes code more maintainable.

## Sub-tasks
- [ ] Identify all SQL queries using `.format()`
- [ ] Refactor SELECT_APPLIED_JOB_IDS_BY_COMPANY
- [ ] Refactor SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT
- [ ] Update all callers to use parameterized queries
- [ ] Write tests for refactored queries
- [ ] Run SQL injection tests
- [ ] Security audit
- [ ] Fix any issues

## Completed
[ ] Pending / [x] Completed

