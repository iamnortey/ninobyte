# Example 001: Vague Request → Implementation Plan

Demonstrates how the skill transforms a vague user request into a structured implementation plan.

---

## User Input

```
Mode: Implementation Planning

I want to add user preferences to our app.
```

---

## Expected Output

```markdown
## Implementation Plan: User Preferences Feature

### Requirements Summary
Add a user preferences system allowing users to customize their application experience. Specific preferences not defined—clarification needed.

### Assumptions
- ASSUMPTION: Web application with authenticated users
- ASSUMPTION: Existing user account system
- ASSUMPTION: Preferences should persist across sessions
- ASSUMPTION: Both frontend and backend changes required

### Open Questions (Priority)
Before proceeding, please clarify:
1. What specific preferences should users be able to set?
   - Notification settings (email, push, SMS)?
   - Display preferences (theme, language, timezone)?
   - Privacy settings?
   - Feature-specific settings?
2. What is your tech stack (frontend framework, backend, database)?
3. Should preferences sync across devices?
4. Are there any existing preference patterns in the codebase?
5. Are there compliance requirements (GDPR preference storage)?

---

### Preliminary Epic Structure

*Note: This will be refined after clarifying questions are answered.*

#### Epic 1: Backend Preferences Infrastructure
**Story 1.1**: Design preferences data model
- Size: M
- Tasks:
  - [ ] Define preference schema (key-value? structured?)
  - [ ] Design database table/collection
  - [ ] Plan for future preference additions
- Acceptance Criteria:
  - [ ] Schema supports planned preference types
  - [ ] Schema is extensible for future preferences
- Dependencies: Answers to clarifying questions

**Story 1.2**: Create preferences API endpoints
- Size: M
- Tasks:
  - [ ] GET /api/users/{id}/preferences
  - [ ] PUT /api/users/{id}/preferences
  - [ ] PATCH /api/users/{id}/preferences (partial update)
  - [ ] Add authentication/authorization checks
- Acceptance Criteria:
  - [ ] Only authenticated user can access own preferences
  - [ ] API follows existing patterns
- Dependencies: Story 1.1

#### Epic 2: Frontend Preferences UI
**Story 2.1**: Create preferences settings page
- Size: L
- Tasks:
  - [ ] Design preferences UI/UX
  - [ ] Implement settings page component
  - [ ] Connect to preferences API
  - [ ] Add loading/error states
- Acceptance Criteria:
  - [ ] Users can view current preferences
  - [ ] Users can modify preferences
  - [ ] Changes persist after page refresh
- Dependencies: Story 1.2

**Story 2.2**: Apply preferences throughout app
- Size: M-L (depends on preference types)
- Tasks:
  - [ ] Implement preference consumption hooks/context
  - [ ] Apply preferences to relevant components
  - [ ] Handle preference loading on app init
- Acceptance Criteria:
  - [ ] Preferences affect app behavior as expected
  - [ ] Graceful handling of missing/default preferences
- Dependencies: Story 2.1

#### Epic 3: Testing & Documentation
**Story 3.1**: Add test coverage
- Size: M
- Tasks:
  - [ ] Unit tests for preference logic
  - [ ] API integration tests
  - [ ] Frontend component tests
- Acceptance Criteria:
  - [ ] Critical paths have test coverage
  - [ ] Tests pass in CI
- Dependencies: Epic 1, Epic 2

### Technical Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Preference schema changes frequently | Medium | Design extensible schema from start |
| Performance impact of loading preferences | Low | Cache preferences client-side, lazy load non-critical |
| Migration of existing users | Medium | Default values for users without preferences |

### Suggested Sequence
1. **Answer clarifying questions** — Critical for accurate planning
2. **Story 1.1** — Data model informs everything else
3. **Story 1.2** — API enables frontend work
4. **Story 2.1** — Core UI
5. **Story 2.2** — Feature integration
6. **Story 3.1** — Parallel with 2.1/2.2

### Notes
- This plan is preliminary pending clarification
- Sizes may change based on actual tech stack and requirements
- Consider privacy/GDPR requirements early in design
```

---

## Key Behaviors Demonstrated

1. **Clarifying questions before diving in** — Didn't assume specifics
2. **Assumptions clearly marked** — Transparent about what was assumed
3. **Structured breakdown** — Epics, stories, tasks, acceptance criteria
4. **No time estimates** — Only relative sizing (S/M/L)
5. **Risks identified** — With likelihood and mitigation
6. **Suggested sequence** — Logical ordering with rationale
7. **Actionable next step** — Answer questions before proceeding
