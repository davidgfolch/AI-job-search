# Task ID: 1.2
# Title: Add CV Match Score Explanation
# Status: [ ] Pending
# Priority: critical
# Owner: Frontend Team
# Estimated Effort: 6h

## Description
Add explanation tooltip/modal explaining how CV match percentage is calculated. The explanation must be visible when hovering/clicking match score, explain the 5 factors (skills 40%, experience 25%, optional skills 15%, education 10%, industry knowledge 10%), and mention AI limitations. This task addresses EU AI Act Article 13 - Transparency requirements.

## Dependencies
- [ ] Task ID: 1

## Testing Instructions
1. Verify tooltip/modal appears on hover/click of match score
2. Verify all 5 factors are explained correctly
3. Verify AI limitations are mentioned
4. Test tooltip/modal on different devices
5. Test accessibility (keyboard navigation, screen readers)
6. Verify explanation is clear and understandable

## Security Review
- Ensure explanation doesn't expose proprietary algorithm details
- Verify no sensitive user data is exposed in explanation

## Risk Assessment
- Users may not understand how scores are calculated (transparency risk)
- Missing explanation violates EU AI Act Article 13
- Non-compliance could result in regulatory fines

## Acceptance Criteria
- [ ] Explanation visible when hovering/clicking match score
- [ ] Explanation includes all 5 factors with correct percentages:
  - Required skills match (40% weight)
  - Experience level (25% weight)
  - Optional skills (15% weight)
  - Education/certifications (10% weight)
  - Industry knowledge (10% weight)
- [ ] AI limitations are mentioned
- [ ] Explanation is accessible (keyboard and screen reader compatible)
- [ ] Explanation is clear and understandable

## Definition of Done
- [ ] CVMatchExplanation component created
- [ ] Tooltip/modal integrated into JobCard.tsx
- [ ] All 5 factors explained with percentages
- [ ] AI limitations section added
- [ ] Accessibility testing passed
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: Tooltip/modal functional, all factors explained, limitations mentioned, accessibility tests passing
- **Observable Outcomes**: Users can understand how match scores are calculated, aware of AI limitations
- **Quality Attributes**: Accessible, clear, comprehensive explanation
- **Completion Indicators**: CVMatchExplanation component created and integrated, all content present

## Notes
The explanation should be user-friendly and avoid overly technical language. Consider using visual aids (progress bars, icons) to illustrate the factors.

## Strengths
Critical for transparency compliance. Helps users understand and trust the AI system. Required for EU AI Act Article 13 compliance.

## Sub-tasks
- [ ] Design explanation component (tooltip/modal)
- [ ] Create CVMatchExplanation.tsx component
- [ ] Integrate into JobCard.tsx
- [ ] Add explanation content for all 5 factors
- [ ] Add AI limitations section
- [ ] Test accessibility
- [ ] Test on different devices

## Completed
[ ] Pending / [x] Completed

