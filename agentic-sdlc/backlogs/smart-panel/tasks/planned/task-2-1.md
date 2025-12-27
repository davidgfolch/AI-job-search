# Task ID: 2.1
# Title: Create Backend API for Apply Letter Generation
# Status: [x] Pending / [ ] Completed
# Priority: high
# Owner: Backend Team
# Estimated Effort: 4h

## Description
Create a simple backend API endpoint for apply letter generation. MVP:
- Endpoint: POST /api/jobs/{id}/apply-letter
- Accept: job ID (from URL), language (from body)
- Use existing aiEnrich/CrewAI infrastructure (reuse LLM setup)
- Generate letter using CV + job details
- Return text (max 2000 words - truncate if needed)
- Basic error handling

Reuse existing patterns from aiEnrich - don't overcomplicate. Can add a simple function in backend or extend aiEnrich.

## Dependencies
- [ ] Task ID: 1.4 (Apply Letter Generator UI should exist)

## Testing Instructions
- Test API endpoint with valid job ID and language
- Test with invalid job ID
- Test with invalid language
- Test word limit enforcement
- Test error handling
- Test timeout handling (generation can take time)
- Test with different languages

## Security Review
- Validate input parameters
- Ensure no SQL injection vulnerabilities
- Verify proper authentication/authorization if needed
- Ensure CV content is not exposed inappropriately

## Risk Assessment
- Long generation times might cause timeout issues
- LLM errors not properly handled
- Word limit not enforced server-side

## Acceptance Criteria
- [ ] API endpoint created (e.g., POST /api/jobs/{id}/apply-letter)
- [ ] Endpoint accepts job ID and language parameters
- [ ] Endpoint generates apply letter using CV and job details
- [ ] Generated letter respects 2000 word limit
- [ ] Error handling implemented
- [ ] Timeout handling implemented
- [ ] API documentation updated
- [ ] Endpoint tested with various inputs

## Definition of Done
- [ ] API endpoint implemented
- [ ] Integration with LLM service working
- [ ] Word limit enforced
- [ ] Error handling implemented
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] API documentation updated
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Quantitative Metrics**: API response time < 30s (p95), 0 critical security vulnerabilities
- **Verification Criteria**: Endpoint returns valid letter, word limit enforced, errors handled
- **Observable Outcomes**: API responds correctly, generates appropriate letters
- **Quality Attributes**: Secure, well-tested, documented

## Strengths
Enables automated apply letter generation

## Notes
Should reuse existing aiEnrich infrastructure and CrewAI setup

## Sub-tasks
- [ ] Add endpoint to backend API (reuse existing patterns)
- [ ] Create simple generation function (reuse aiEnrich LLM setup)
- [ ] Add word limit (truncate to 2000 words)
- [ ] Add basic error handling
- [ ] Test manually (unit tests optional for MVP)

## Completed
[ ] Pending / [x] Completed

