# Test Fixture 001: Architecture Review Request

**Fixture ID**: FIXTURE-001
**Mode**: Architecture Review
**Purpose**: Verify Architecture Review mode produces structured output with all required sections and enforces security policy

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
6. `### Security Assessment` section (NEW in v0.1.1) with:
   - Authentication assessment
   - Authorization assessment
   - Encryption assessment
   - Secrets Management assessment
7. `### Risks` section
8. `### Recommendations` numbered list
9. `### Questions for Stakeholders` section

The output MUST identify these specific concerns as **CRITICAL** per security policy:
- Single EC2 instance (single point of failure)
- JWT in localStorage (XSS vulnerability - MUST flag as CRITICAL)
- Shared database (single point of failure, coupling)

The output MUST flag authentication concerns:
- JWT in localStorage is a security anti-pattern
- Recommend httpOnly cookies instead

---

## Security Policy Verification

Per SKILL.md Security Policy, the output MUST:
- [ ] Flag JWT in localStorage as CRITICAL (not just HIGH)
- [ ] Recommend established patterns (httpOnly cookies) over insecure defaults
- [ ] Include Security Assessment section
- [ ] Flag single points of failure as CRITICAL

---

## Verification Criteria

- [ ] All required sections present including Security Assessment
- [ ] At least 3 concerns identified
- [ ] CRITICAL concerns: JWT localStorage, single EC2 instance
- [ ] HIGH concerns: shared database, no caching
- [ ] Recommendations are actionable with priority labels
- [ ] Security Assessment covers auth, authz, encryption, secrets
