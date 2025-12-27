# Task ID: 2
# Title: Epic 2: Backend - Apply Letter Generation API
# Status: [x] Pending / [ ] Completed
# Priority: high
# Owner: Backend Team
# Estimated Effort: 5h

## Description
Backend implementation for apply letter generation. Create API endpoint (POST /api/jobs/{id}/apply-letter) that uses existing aiEnrich/CrewAI infrastructure (apps/aiEnrich) to generate personalized apply letters using CV content (apps/aiEnrich/cv/cv.pdf) and job details from database. This epic includes: (1) creating the API endpoint in the backend service, (2) implementing letter generation using CrewAI/Ollama LLM, (3) adding language parameter support, and (4) enforcing 2000 word limit. Reuse existing LLM configuration and patterns from cvMatcher.py.

## Dependencies
- [ ] Task ID: 1 (Frontend UI needs to exist before backend integration)

## Testing Instructions
- Test API endpoint with valid job ID and language
- Test with invalid job ID (should return error)
- Test with invalid language (should validate and reject)
- Test letter generation with different languages
- Test word limit enforcement (max 2000 words)
- Test timeout handling (generation can take 5-10 minutes)
- Test error handling for LLM failures

## Security Review
- Validate input parameters
- Ensure no SQL injection vulnerabilities
- Verify proper authentication/authorization if needed
- Ensure CV content is not exposed inappropriately

## Risk Assessment
- Long generation times might cause timeout issues
- LLM errors not properly handled
- Word limit not enforced server-side
- Delays in this phase may impact overall project timeline

## Acceptance Criteria
- [ ] API endpoint created (POST /api/jobs/{id}/apply-letter)
- [ ] Endpoint accepts job ID and language parameters
- [ ] Letter generation uses CV and job details
- [ ] Language parameter passed to LLM prompt
- [ ] Generated letter respects 2000 word limit
- [ ] Error handling implemented for all failure cases
- [ ] Timeout handling implemented

## Definition of Done
- [ ] Both subtasks (2.1, 2.2) completed
- [ ] API endpoint implemented and tested
- [ ] Language support integrated
- [ ] Word limit enforced
- [ ] Error handling implemented
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Quantitative Metrics**: API response time < 30s (p95), 0 critical security vulnerabilities
- **Verification Criteria**: Endpoint returns valid letter, word limit enforced, errors handled correctly
- **Observable Outcomes**: API responds correctly, generates appropriate letters in requested language
- **Quality Attributes**: Secure, well-tested, documented, follows existing patterns
- **Completion Indicators**: Both subtasks completed, endpoint tested, documentation updated

## Strengths
Essential for achieving project goals and success criteria. Enables automated apply letter generation with language support.

## Notes
Phase 2 of 3: Backend: Create apply letter generation API endpoint

## Sub-tasks
- [ ] [Task 2.1: Create Backend API for Apply Letter Generation](task-2-1.md) (4h)
- [ ] [Task 2.2: Add Language Selection for Apply Letter](task-2-2.md) (1h)

## Completed
[ ] Pending
