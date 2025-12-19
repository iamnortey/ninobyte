# Code Review Checklist

Use this checklist when operating in **Code Review** mode.

---

## 1. Correctness

- [ ] Does the code do what it's supposed to do?
- [ ] Are edge cases handled?
- [ ] Are error conditions handled appropriately?
- [ ] Is the logic correct (no off-by-one, null checks, etc.)?
- [ ] Are return values and types correct?

## 2. Security

- [ ] Is user input validated and sanitized?
- [ ] Are SQL queries parameterized (no SQL injection)?
- [ ] Is output encoded (no XSS)?
- [ ] Are authentication/authorization checks in place?
- [ ] Are secrets hardcoded? (CRITICAL if yes)
- [ ] Is sensitive data logged? (Should not be)
- [ ] Are dependencies up to date and free of known vulnerabilities?
- [ ] Is the principle of least privilege followed?

## 3. Performance

- [ ] Are there obvious performance issues (N+1 queries, unbounded loops)?
- [ ] Is caching used appropriately?
- [ ] Are database queries optimized (proper indexes assumed)?
- [ ] Are large collections handled efficiently (pagination, streaming)?
- [ ] Is memory usage reasonable?

## 4. Readability & Maintainability

- [ ] Is the code easy to understand?
- [ ] Are variable/function names descriptive?
- [ ] Is the code properly formatted and consistent?
- [ ] Are complex sections commented (but not over-commented)?
- [ ] Is the code DRY (Don't Repeat Yourself)?
- [ ] Are functions/methods appropriately sized?

## 5. Error Handling

- [ ] Are exceptions/errors caught at appropriate levels?
- [ ] Are error messages helpful (without leaking sensitive info)?
- [ ] Is there proper cleanup in error paths (resources, connections)?
- [ ] Are errors logged appropriately?
- [ ] Is the fail-fast principle applied where appropriate?

## 6. Testing

- [ ] Are there tests for this code?
- [ ] Do tests cover happy path and edge cases?
- [ ] Are tests readable and maintainable?
- [ ] Is test coverage adequate for the risk level?
- [ ] Are mocks/stubs used appropriately?

## 7. Architecture & Design

- [ ] Does this follow existing patterns in the codebase?
- [ ] Is the responsibility of each function/class clear?
- [ ] Are dependencies injected rather than hardcoded?
- [ ] Is the code loosely coupled?
- [ ] Does this introduce technical debt? (Flag if yes)

## 8. API Design (if applicable)

- [ ] Is the API intuitive and consistent?
- [ ] Are request/response schemas validated?
- [ ] Is versioning considered?
- [ ] Are appropriate HTTP methods/status codes used?
- [ ] Is the API documented?

## 9. Concurrency (if applicable)

- [ ] Are shared resources protected?
- [ ] Are there potential race conditions?
- [ ] Is the concurrency model appropriate?
- [ ] Are deadlocks possible?

## 10. Documentation

- [ ] Are public APIs documented?
- [ ] Are complex algorithms explained?
- [ ] Is the README updated if needed?
- [ ] Are breaking changes documented?

---

## Issue Severity

| Level | Symbol | Definition |
|-------|--------|------------|
| Critical | 🔴 | Security vulnerability, data loss, crash. Must fix. |
| Important | 🟡 | Bug, significant issue, or anti-pattern. Should fix. |
| Minor | 🔵 | Style, suggestion, or nice-to-have. Consider fixing. |

---

## Feedback Principles

1. **Be specific**: Point to exact lines, suggest exact fixes
2. **Be constructive**: Explain why, not just what
3. **Be kind**: Assume good intent, praise good patterns
4. **Be actionable**: Every issue should have a clear resolution path
5. **Prioritize**: Not all issues are equal; help author focus

---

## Output Reminders

After completing review:
1. Overall verdict: Approve / Request Changes / Needs Discussion
2. Acknowledge what's good
3. Issues grouped by severity with line numbers and suggestions
4. Security considerations section
5. Testing observations
6. Questions needing clarification
