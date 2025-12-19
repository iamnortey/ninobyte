# Architecture Review Checklist

Use this checklist when operating in **Architecture Review** mode.

---

## 1. Requirements Alignment

- [ ] Are functional requirements clearly addressed?
- [ ] Are non-functional requirements (performance, scalability, availability) considered?
- [ ] Are compliance/regulatory requirements identified and addressed?
- [ ] Is the scope well-defined with clear boundaries?

## 2. Component Design

- [ ] Are components appropriately sized (not too large, not too granular)?
- [ ] Is each component's responsibility clear and single-purpose?
- [ ] Are component boundaries well-defined?
- [ ] Are dependencies between components minimized?
- [ ] Is the component inventory complete (nothing hidden)?

## 3. Data Architecture

- [ ] Is data ownership clear for each domain?
- [ ] Are data flows documented?
- [ ] Is data persistence strategy appropriate (SQL, NoSQL, cache)?
- [ ] Are data consistency requirements identified (strong, eventual)?
- [ ] Is data partitioning/sharding strategy defined if needed?
- [ ] Are backup and recovery strategies defined?

## 4. Integration & Communication

- [ ] Are integration patterns appropriate (sync, async, event-driven)?
- [ ] Are API contracts defined?
- [ ] Is service discovery addressed?
- [ ] Are circuit breakers/retry policies considered?
- [ ] Is the communication protocol appropriate (REST, gRPC, GraphQL)?

## 5. Scalability

- [ ] Can components scale independently?
- [ ] Are stateless designs preferred where possible?
- [ ] Are bottlenecks identified?
- [ ] Is horizontal scaling supported?
- [ ] Are caching strategies defined?

## 6. Reliability & Availability

- [ ] Are single points of failure identified and mitigated?
- [ ] Is redundancy built in for critical components?
- [ ] Are failover strategies defined?
- [ ] Are SLOs/SLAs defined?
- [ ] Is graceful degradation supported?

## 7. Security

- [ ] Is authentication strategy defined?
- [ ] Is authorization model clear (RBAC, ABAC)?
- [ ] Is data encrypted in transit and at rest?
- [ ] Are secrets management practices defined?
- [ ] Is input validation enforced at boundaries?
- [ ] Are audit logging requirements addressed?
- [ ] Is the attack surface minimized?

## 8. Observability

- [ ] Is logging strategy defined?
- [ ] Are metrics collection points identified?
- [ ] Is distributed tracing supported?
- [ ] Are health checks implemented?
- [ ] Are alerting thresholds defined?

## 9. Deployment & Operations

- [ ] Is the deployment strategy defined (blue-green, canary, rolling)?
- [ ] Is CI/CD pipeline considered?
- [ ] Are environment configurations managed?
- [ ] Is infrastructure as code used?
- [ ] Are rollback procedures defined?

## 10. Maintainability

- [ ] Is the architecture documented?
- [ ] Are coding standards defined?
- [ ] Is the testing strategy clear?
- [ ] Is technical debt tracked?
- [ ] Are upgrade paths considered?

---

## Severity Ratings

When identifying issues, rate severity:

| Rating | Definition |
|--------|------------|
| **CRITICAL** | Blocks launch, causes data loss, or major security vulnerability |
| **HIGH** | Significant impact on reliability, scalability, or security |
| **MEDIUM** | Impacts maintainability or operational efficiency |
| **LOW** | Minor improvements, nice-to-haves |

---

## Output Reminders

After completing review:
1. Summarize in 1-2 sentences
2. List strengths (what's done well)
3. Table of concerns with priority, impact, recommendation
4. Risks with likelihood/impact
5. Prioritized recommendations
6. Questions needing stakeholder input
