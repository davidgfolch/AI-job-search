# Task ID: 2.2
# Title: Add Language Selection for Apply Letter
# Status: [x] Pending / [ ] Completed
# Priority: medium
# Owner: Backend Team
# Estimated Effort: 1h

## Description
Add language support to apply letter generation. MVP:
- Start with common languages: English, Spanish, French, German, Italian, Portuguese, Dutch, Polish
- Pass language parameter to LLM prompt (e.g., "Generate in {language}")
- Simple validation (reject invalid language codes)

For MVP, don't need to research all possible languages - just support the common ones. Can expand later.

## Dependencies
- [ ] Task ID: 2.1

## Testing Instructions
- Test with each available language
- Verify letters are generated in correct language
- Test with invalid language codes
- Test language validation

## Security Review
- Validate language parameter to prevent injection
- Ensure language codes are safe

## Risk Assessment
- Some languages might not be well-supported by models
- Language validation might be incomplete

## Acceptance Criteria
- [ ] Language parameter passed to generation function
- [ ] Language included in LLM prompt
- [ ] Basic language validation (reject unknown languages)
- [ ] Common languages work (English, Spanish, French, etc.)

## Definition of Done
- [ ] Language list researched and documented
- [ ] Language parameter integrated into service
- [ ] Language validation implemented
- [ ] Testing with multiple languages completed
- [ ] Language list exposed to frontend (API or config)
- [ ] Code reviewed and approved
- [ ] All acceptance criteria met

## Measurable Outcomes
- **Verification Criteria**: Letters generated in correct language, invalid languages rejected
- **Quantitative Metrics**: Support for all major languages from available models
- **Observable Outcomes**: Language selection works, letters in correct language
- **Quality Attributes**: Well-documented, validated

## Strengths
Enables multilingual apply letter generation

## Notes
Need to research which languages are supported by llama3.2 and other available Ollama models. Common languages: English, Spanish, French, German, Italian, Portuguese, Dutch, Polish, etc.

## Sub-tasks
- [ ] Add language to generation prompt
- [ ] Create simple language list (hardcode 8-10 common languages)
- [ ] Add basic validation
- [ ] Test with 2-3 languages

## Completed
[ ] Pending / [x] Completed

