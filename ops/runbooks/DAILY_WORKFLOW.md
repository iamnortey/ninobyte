# Ninobyte Daily Development Workflow

> Deterministic PR-based workflow for the Ninobyte monorepo.
> Created: 2025-12-20 | Last validated: v0.2.3

---

## Quick Reference

```
Branch naming:   feat|fix|chore|docs|ci|refactor/short-description
Commit format:   type(scope): description
PR merge:        gh pr merge --auto --squash
```

---

## 1. Pre-Work Sync

```zsh
cd /Users/isaacnortey/Developer/ninobyte

git checkout main
git pull origin main
git fetch --prune
```

Verify clean state:

```zsh
git status
git log --oneline -3
```

---

## 2. Branch Creation

Use variables to avoid zsh redirection issues:

```zsh
branch_type="feat"
branch_desc="my-feature-name"
branch="${branch_type}/${branch_desc}"

git checkout -b "$branch"
```

**Allowed prefixes:** `feat/`, `fix/`, `chore/`, `docs/`, `ci/`, `refactor/`, `test/`, `release/`

---

## 3. Development + Commit Hygiene

### Commit Message Format

```
type(scope): short description

Optional longer description.
```

**Types:** feat, fix, chore, docs, ci, refactor, test, perf, style

### Atomic Commits

```zsh
git add -p
git commit -m "feat(airgap): add path validation"
```

---

## 4. Pre-Push Validation

Run before every push:

```zsh
python scripts/ci/validate_artifacts.py
```

Run tests (if applicable):

```zsh
pytest products/mcp-servers/ninobyte-airgap/tests/ -v
pytest products/opspack/tests/ -v
```

Secret scan sanity check:

```zsh
git diff --cached | grep -iE "(password|secret|api[_-]?key|token|credential)" || echo "No secrets detected"
```

---

## 5. Push + PR Creation

```zsh
git push -u origin "$branch"
```

Create PR with descriptive title/body:

```zsh
pr_title="feat(scope): short description"
pr_body="## Summary
- What this PR does

## Testing
- How it was tested"

gh pr create --title "$pr_title" --body "$pr_body"
```

For simple PRs, use auto-fill:

```zsh
gh pr create --fill
```

---

## 6. Check Gating + Auto-Merge

View PR status:

```zsh
gh pr view --web
```

Enable auto-merge (merges when checks pass):

```zsh
gh pr merge --auto --squash
```

Or wait and merge manually:

```zsh
gh pr checks
gh pr merge --squash
```

---

## 7. Post-Merge Cleanup

```zsh
git checkout main
git pull origin main
git branch -d "$branch"
git fetch --prune
```

Verify:

```zsh
git log --oneline -5
git branch -a
```

---

## 8. Tag + Release Creation

**Only after merging to main and confirming correctness.**

### Create Annotated Tag

```zsh
version="0.2.4"
tag_msg="v${version}: OpsPack contract hardening

Highlights:
- Adds tests to enforce interface contract invariants
- Reinforces governance-as-code posture"

git tag -a "v${version}" -m "$tag_msg"
git push origin "v${version}"
```

### Create GitHub Release

```zsh
version="0.2.4"
release_title="v${version} - OpsPack Contract Hardening"
release_notes="## Highlights
- Adds tests to enforce interface contract invariants
- Reinforces governance-as-code posture for OpsPack evolution

## Changes
- See commit log for full details"

gh release create "v${version}" --title "$release_title" --notes "$release_notes"
```

---

## Pre-Commit Checklist

- [ ] Branch created from latest main
- [ ] Branch name follows convention: `type/short-description`
- [ ] Commits are atomic and follow format
- [ ] `validate_artifacts.py` passes
- [ ] `pytest` passes (if tests exist for changed code)
- [ ] No secrets in diff: `git diff | grep -iE "(password|secret|api[_-]?key|token|credential)"`
- [ ] PR created with meaningful title/body
- [ ] Checks are green before merge

---

## Common Mistakes to Avoid

| Mistake | Prevention |
|---------|------------|
| Creating branch with no diff | Always make changes before creating PR |
| Placeholder release notes | Write release notes BEFORE running `gh release create` |
| Force pushing to main | Never. Always use PR workflow |
| Skipping validation | Run `validate_artifacts.py` before every push |
| Stale local branches | Run `git fetch --prune` daily |

---

## Emergency: Undo Bad Tag/Release

If you create a tag with bad metadata:

```zsh
bad_version="0.2.4"

gh release delete "v${bad_version}" --yes
git push origin --delete "v${bad_version}"
git tag -d "v${bad_version}"
```

Then recreate with correct metadata.

---

## Repo Health Check (End of Day)

```zsh
echo "=== Status ===" && git status
echo "=== Branch ===" && git branch --show-current
echo "=== HEAD ===" && git log --oneline -1
echo "=== Open PRs ===" && gh pr list --state open
echo "=== Latest Tags ===" && git tag --sort=-creatordate | head -5
echo "=== Remote Branches ===" && git branch -r | wc -l
```

---

## Default Loop (Claude Code Enterprise Mode)

When using Claude Code for development, follow the enterprise delivery loop:

```
/enterprise → plan → implement → /audit → /compliance → /red-team → PR
```

### Step-by-Step

1. **Enable Enterprise Mode**
   ```
   /enterprise
   ```
   Activates Safety Harness with approval-gated destructive operations.

2. **Plan Phase**
   - State your intent clearly
   - Claude will produce a structured implementation plan
   - Review and refine before proceeding

3. **Implementation**
   - Follow TDD where applicable
   - Commit atomically
   - Use conventional commit messages

4. **Quality Gates**
   ```
   /audit        # Security + code quality review
   /compliance   # Secrets, PII, licensing checks
   /red-team     # Adversarial breakage analysis
   ```

5. **PR Creation**
   - Include quality gate evidence in PR description
   - Reference audit artifacts if available

### Safety Harness Commands

| Command | Purpose |
|---------|---------|
| `/enterprise` | Enable full Safety Harness |
| `/vibe` | Switch to Rapid Vibe Mode (stamps required) |
| `/status` | Show current mode + pending approvals |
| `/change-plan` | Propose destructive operation |
| `/approve APPROVE:<id>` | Approve a change plan |

### Destructive Operations Requiring Approval

- `git push`, `git push -f`
- `rm`, `rm -rf`
- `chmod`, `chown`
- Database migrations
- Infrastructure changes (terraform, kubectl)

---

## Files Referenced

- `scripts/ci/validate_artifacts.py` - Artifact validation
- `products/mcp-servers/ninobyte-airgap/tests/` - AirGap tests
- `products/opspack/tests/` - OpsPack tests
- `ops/release/RELEASE_CHECKLIST.md` - Full release checklist
- `ops/runbooks/VIBE_PILOT_RUNBOOK.md` - Enterprise delivery validation
