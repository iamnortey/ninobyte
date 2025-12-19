# Test Fixture 001: Architecture Review Request

**Fixture ID**: FIXTURE-001
**Mode**: Architecture Review
**Purpose**: Verify Architecture Review mode produces structured output with all required sections

---

## Input

```
Mode: Architecture Review

Review this e-commerce system architecture:

Components:
- Web Frontend (React SPA)
- API Gateway (nginx)
- User Service (Node.js, PostgreSQL)
- Product Service (Node.js, PostgreSQL)
- Order Service (Node.js, PostgreSQL)
- Payment Service (Node.js, Stripe integration)
- Notification Service (Node.js, SendGrid/Twilio)
- Message Queue (RabbitMQ)

All services run in Docker containers on a single EC2 instance.
Database is a single PostgreSQL instance shared by all services.
No caching layer.
No CDN.
Authentication uses JWT stored in localStorage.
```

---

## Expected Behavior

The output MUST include:
1. `## Architecture Review:` header with system name
2. `### Summary` section (1-2 sentences)
3. `### Components Reviewed` list
4. `### Strengths` section with bullet points
5. `### Concerns` table with Priority/Concern/Impact/Recommendation columns
6. `### Risks` section
7. `### Recommendations` numbered list
8. `### Questions for Stakeholders` section

The output MUST identify these specific concerns:
- Single EC2 instance (single point of failure)
- Shared database (coupling, scaling limitation)
- No caching (performance)
- No CDN (latency, load)
- JWT in localStorage (XSS vulnerability)

---

## Verification Criteria

- [ ] All required sections present
- [ ] At least 3 concerns identified
- [ ] Concerns include severity ratings
- [ ] Recommendations are actionable
- [ ] Security issue (JWT localStorage) flagged as HIGH priority
