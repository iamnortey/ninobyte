# Tagging Policy

This repository uses tag semantics to disambiguate platform releases, GA releases, and skill pack releases.

## Tag Types

### Platform tags
- Format: `vX.Y.Z`
- Meaning: platform-level release tags (not GA unless explicitly indicated)

### GA releases
- Format: `vX.Y.Z-ga-core` or `vX.Y.Z-ga-portfolio`
- Meaning: GA release lines for core or portfolio releases

### Skill pack releases
- Format: `vX.Y.Z-skill-<name>`
- Meaning: a skill pack release (e.g., `v1.0.0-skill-sdb`)

## Rules
- Tags must be accompanied by a tag message that states the release type.
- Changelog entries must link to the correct release class.
- If a historical tag conflicts with the current policy, document it as clarification rather than rewriting history.

