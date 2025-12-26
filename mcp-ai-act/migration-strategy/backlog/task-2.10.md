# Task ID: 2.10
# Title: Add Manual Override Capability
# Status: [ ] Pending
# Priority: high
# Owner: Frontend/Backend Team
# Estimated Effort: 8h

## Description
Allow users to manually adjust match criteria weights. This includes allowing users to adjust weights, calculating custom match scores, and logging overrides. This task addresses EU AI Act Article 14 - Human Oversight requirements.

## Dependencies
- [ ] Task ID: 2.0

## Testing Instructions
1. Verify users can adjust weights
2. Verify custom match scores are calculated correctly
3. Verify overrides are logged
4. Test weight adjustment UI
5. Test score recalculation
6. Verify logging works

## Security Review
- Ensure override capability doesn't expose system vulnerabilities
- Verify override logging is secure

## Risk Assessment
- Missing override capability violates EU AI Act Article 14
- Users cannot customize AI behavior without this
- Non-compliance could result in regulatory fines

## Acceptance Criteria
- [ ] Users can adjust weights
- [ ] Custom match scores calculated correctly
- [ ] Override is logged
- [ ] Interface is user-friendly
- [ ] Override functionality is accessible

## Definition of Done
- [ ] MatchSettings.tsx component created
- [ ] cv_match.py API updated
- [ ] Weight adjustment UI implemented
- [ ] Custom score calculation implemented
- [ ] Override logging implemented
- [ ] Tests written and passing
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: Weight adjustment functional, custom scores calculated, overrides logged, tests passing
- **Observable Outcomes**: Users can adjust weights, see custom scores, overrides tracked
- **Quality Attributes**: Functional, user-friendly, logged override capability
- **Completion Indicators**: Components created, functionality working, logging verified

## Notes
This gives users control over AI behavior. Consider default weight presets and saving user preferences.

## Strengths
Essential for human oversight compliance. Enables user control over AI. Required for EU AI Act Article 14 compliance.

## Sub-tasks
- [ ] Design weight adjustment interface
- [ ] Create MatchSettings.tsx component
- [ ] Update cv_match.py API
- [ ] Implement weight adjustment
- [ ] Implement custom score calculation
- [ ] Implement override logging
- [ ] Write tests

## Completed
[ ] Pending / [x] Completed

