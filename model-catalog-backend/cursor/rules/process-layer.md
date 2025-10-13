# Decision Framework

## When to Use LLM
✓ Exploratory coding and prototyping
✓ Refactoring existing code
✓ Writing tests and documentation
✓ Debugging and error analysis
✓ Architecture brainstorming
✓ Code review assistance

✗ DON'T use for:
- Final security audits (use for suggestions only)
- Compliance/legal decisions
- Production deployment approvals
- Choosing vendors or making budget decisions

## Validation Rules
Before accepting LLM output:
1. Does it compile/run?
2. Does it handle edge cases?
3. Does it match our security standards?
4. Is it maintainable by the team?
5. Does it solve the actual problem?

## Iteration Protocol
- First pass: Get multiple approaches
- Second pass: Refine chosen approach
- Third pass: Edge cases and error handling
- Final: Documentation and tests

Ask: "What are 3 different ways to solve this? Compare trade-offs."
Not: "Write me X" (one-shot)