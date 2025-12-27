# Task ID: 3.1
# Title: Integrate Apply Letter Generator with Frontend
# Status: [x] Pending / [ ] Completed
# Priority: high
# Owner: Frontend Team
# Estimated Effort: 2h

## Description
Connect the Apply Letter Generator UI to the backend API. MVP:
- Call API when Generate button clicked
- Pass job ID and language
- Show loading state
- Display result in textarea
- Show error if API fails
- Display word count

Keep it simple - basic fetch call, handle response, show result.

## Dependencies
- [ ] Task ID: 1.4 (Apply Letter Generator Tab UI)
- [ ] Task ID: 2.1 (Backend API endpoint)
- [ ] Task ID: 2.2 (Language support)

## Testing Instructions
- Test full flow: select language → click generate → receive letter
- Test error scenarios (API errors, network errors)
- Test loading states
- Test word count display
- Test with different languages
- Test with different jobs

## Security Review
- Ensure API calls are properly authenticated if needed
- Verify no sensitive data in API requests/responses

## Risk Assessment
- API integration issues
- Error handling might not cover all cases
- Long generation times might cause UX issues

## Acceptance Criteria
- [ ] Generate button calls API
- [ ] Job ID and language sent correctly
- [ ] Loading state shown
- [ ] Letter displayed in textarea
- [ ] Error shown if API fails
- [ ] Word count displayed
- [ ] End-to-end works

## Definition of Done
- [ ] API integration implemented
- [ ] Error handling implemented
- [ ] Loading states implemented
- [ ] Word count validation implemented
- [ ] End-to-end testing completed
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: Full flow works, errors handled, word count validated
- **Observable Outcomes**: Smooth user experience, clear feedback
- **Quality Attributes**: Well-integrated, user-friendly

## Strengths
Completes the apply letter generation feature

## Notes
Should handle long generation times gracefully (show progress, allow cancellation if needed)

## Sub-tasks
- [ ] Add API call function (fetch)
- [ ] Connect Generate button
- [ ] Handle response (success/error)
- [ ] Add word count display
- [ ] Test manually

## Completed
[ ] Pending / [x] Completed

