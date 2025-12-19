# Incident Triage Runbook

Use this runbook when operating in **Incident Triage** mode.

---

## Phase 1: Gather Information

### Essential Questions
1. **What is happening?** (Symptoms, error messages)
2. **When did it start?** (Timestamp, correlation with changes)
3. **Who/what is affected?** (Users, services, regions)
4. **What changed recently?** (Deployments, config changes, traffic)
5. **What have you tried?** (Actions already taken)

### Information to Collect
- Error messages and logs
- Metrics/graphs showing the issue
- Timeline of events
- Recent deployments or changes
- Customer reports
- Alert details

---

## Phase 2: Classify Severity

| Severity | Impact | Response |
|----------|--------|----------|
| **SEV1** | Complete outage, data loss, security breach | All hands, immediate escalation |
| **SEV2** | Major feature broken, significant user impact | Primary on-call + backup |
| **SEV3** | Degraded service, workaround available | Primary on-call |
| **SEV4** | Minor issue, low impact | Normal priority |

### Severity Decision Factors
- Number of users affected
- Revenue/business impact
- Data integrity risk
- Security implications
- Duration of issue

---

## Phase 3: Generate Hypotheses

### Common Root Causes
1. **Recent deployment** — Code bug, config error
2. **Infrastructure** — Server failure, network issue, capacity
3. **Dependencies** — External service degradation
4. **Data** — Corrupted data, migration issue
5. **Traffic** — Unexpected load, DDoS
6. **Security** — Attack, compromised credentials
7. **Configuration** — Misconfiguration, expired cert/token

### Hypothesis Template
```
Hypothesis: [Brief description]
Confidence: High / Medium / Low
Evidence For: [What supports this]
Evidence Against: [What contradicts this]
To Validate: [Specific diagnostic step]
```

### Rank hypotheses by:
1. Evidence strength
2. Ease of validation
3. Blast radius if true

---

## Phase 4: Investigate

### Diagnostic Commands (Examples)
```bash
# Check service health
kubectl get pods -n [namespace]
curl -I https://[service]/health

# Check logs
kubectl logs [pod] --tail=100
grep ERROR /var/log/[service].log

# Check metrics
# (Use your observability platform)

# Check recent changes
git log --oneline -10
kubectl rollout history deployment/[name]
```

### Investigation Principles
- **Time-box investigations**: Don't spend >10 minutes on a hypothesis before pivoting
- **Communicate**: Update stakeholders every 15-30 minutes
- **Document**: Log what you checked and found
- **Don't make it worse**: Avoid risky actions without approval

---

## Phase 5: Mitigate

### Immediate Mitigation Options
| Action | When to Use | Risk |
|--------|-------------|------|
| Rollback | Recent deployment caused issue | May lose new features |
| Scale up | Capacity issue | Cost, may not help |
| Failover | Region/zone failure | Complexity |
| Feature flag off | Specific feature broken | Feature unavailable |
| Block traffic | Attack/abuse | Impacts legitimate users |
| Restart | Process hung/memory leak | Brief downtime |

### Mitigation Principles
1. Prefer reversible actions
2. Mitigation ≠ Root cause fix (that comes later)
3. Document what you did and why
4. Verify mitigation worked

---

## Phase 6: Communicate

### Status Update Template
```
[Incident Title] - Status Update [#N]

Status: Investigating / Mitigating / Monitoring / Resolved
Severity: SEV[X]
Impact: [Who/what is affected]
Start Time: [Timestamp]

Current Status:
[Brief description of what we know and what we're doing]

Next Update: [Time]

For questions: [Contact]
```

### Communication Cadence
- SEV1: Every 15 minutes
- SEV2: Every 30 minutes
- SEV3/4: As significant updates occur

---

## Phase 7: Post-Incident

### Immediate Follow-up
- [ ] Confirm issue is fully resolved
- [ ] Remove any temporary mitigations
- [ ] Notify stakeholders of resolution
- [ ] Document timeline and actions taken

### Post-Incident Review (Schedule within 48 hours)
- What happened?
- How did we detect it?
- How did we respond?
- What went well?
- What could be improved?
- Action items to prevent recurrence

### Blameless Post-mortem Principles
- Focus on systems, not individuals
- Ask "how" not "who"
- Seek improvements, not blame
- Share learnings broadly

---

## Output Reminders

When providing incident triage output:
1. Classification (severity, scope, status)
2. Timeline of known events
3. Symptoms list
4. Ranked hypotheses with confidence and validation steps
5. Recommended immediate actions
6. Investigation steps
7. Post-incident follow-ups
8. Communication draft for stakeholders
