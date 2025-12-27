# Task ID: 1.4
# Title: Implement Apply Letter Generator Tab UI
# Status: [x] Pending / [ ] Completed
# Priority: high
# Owner: Frontend Team
# Estimated Effort: 3h

## Description
Create the "Apply Letter Generator" tab UI. MVP includes:
- Language dropdown (start with common languages: English, Spanish, French, German, Italian, Portuguese, Dutch, Polish)
- "Generate" button (only generates on click, not auto)
- Text area for generated letter (max 2000 words - show word count)
- Loading spinner while generating
- Simple error message display

Keep it simple - basic form with dropdown, button, and textarea.

## Dependencies
- [ ] Task ID: 1.2 (Tabs must exist)
- [ ] Task ID: 1.3 (CV Match Criteria tab for reference)

## Testing Instructions
- Test language selection dropdown
- Test Generate button functionality
- Test loading states
- Test error handling
- Test word count limit (2000 words)
- Test with different languages

## Security Review
- Ensure input validation for language selection
- Verify proper error handling doesn't expose sensitive info

## Risk Assessment
- API errors not properly handled
- Long generation times might cause UX issues
- Word limit not properly enforced

## Acceptance Criteria
- [ ] Language dropdown with common languages (5-10 languages for MVP)
- [ ] Generate button present
- [ ] Generation only on button click
- [ ] Loading state (spinner or "Generating..." text)
- [ ] Text area displays generated letter
- [ ] Word count shown (max 2000)
- [ ] Simple error message display

## Definition of Done
- [ ] ApplyLetterGenerator component created
- [ ] Language dropdown implemented
- [ ] Generate button implemented
- [ ] Loading states implemented
- [ ] Error handling implemented
- [ ] Word count validation implemented
- [ ] Component tested
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: Generate button works, language selection works, word limit enforced
- **Observable Outcomes**: Smooth UI interactions, clear loading/error states
- **Quality Attributes**: User-friendly, responsive

## Strengths
Enables users to generate personalized apply letters

## Notes
Language list should include all languages supported by available LLM models (check Ollama models)

## Sub-tasks
- [ ] Create ApplyLetterGenerator component
- [ ] Add language dropdown (hardcode 5-10 common languages for MVP)
- [ ] Add Generate button
- [ ] Add textarea for letter
- [ ] Add loading state (simple)
- [ ] Add error display (simple)
- [ ] Add word count display

## Completed
[ ] Pending / [x] Completed

