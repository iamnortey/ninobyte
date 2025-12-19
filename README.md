# Ninobyte

Enterprise-grade education and tooling for Anthropic/Claude agent ecosystems.

## Mission

Build the most trusted, implementation-grade resource for Claude Skills, MCP servers, and Claude Code extensions—verified, secure, and reproducible.

## Repository Structure

```
ninobyte/
├── docs/                    # Governance, architecture, tutorials
├── marketplace/             # Curated catalog of products
├── products/                # Skill packs, MCP servers, plugins
├── shared/                  # Reusable schemas, security, tooling
├── tests/                   # Cross-product test infrastructure
├── ops/                     # Runbooks, release process, evidence
└── .github/                 # CI/CD workflows
```

## Products

### v0.1.2 — Senior Developer's Brain

A job system for enterprise software engineering execution. Modes include:
- Architecture Review
- Implementation Planning
- Code Review
- Incident Triage
- ADR Writer

**Canonical Location**: [skills/senior-developer-brain/](skills/senior-developer-brain/)
**Claude Code Plugin**: [products/claude-code-plugins/ninobyte-senior-dev-brain/](products/claude-code-plugins/ninobyte-senior-dev-brain/)

## Getting Started

1. Clone this repository
2. Navigate to a product directory
3. Follow the product's README for installation and usage

## Governance

- [PROJECT_INSTRUCTIONS.md](docs/canonical/PROJECT_INSTRUCTIONS.md) — Mission, policies, validation requirements
- [PINNED_PROJECT_PROMPT.md](docs/canonical/PINNED_PROJECT_PROMPT.md) — Execution contract for AI agents
- [VALIDATION_LOG.md](docs/canonical/VALIDATION_LOG.md) — Official source validation evidence
- [DISTRIBUTION_AND_DISCOVERY.md](docs/distribution/DISTRIBUTION_AND_DISCOVERY.md) — Installation, sync, and discovery

## Security

See [SECURITY.md](SECURITY.md) for security policies, vulnerability reporting, and threat model references.

## License

See [LICENSE](LICENSE)

---

Repo root: `/Users/isaacnortey/Developer/ninobyte`

