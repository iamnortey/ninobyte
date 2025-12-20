# Ninobyte OpsPack - Roadmap

**Last Updated**: December 2024

## Overview

This document outlines the phased implementation plan for OpsPack. All phases maintain the core security constraints: read-only, no network, no shell, deny-by-default.

## Phase 1: Skeleton + Governance (Current)

**Status**: This PR

**Deliverables**:
- Directory structure and package stubs
- Security policy documentation
- Threat model
- Interface contracts (design only)
- Roadmap (this document)

**What is NOT included**:
- No functional code
- No data collection logic
- No evidence pack generation
- No validation gates

## Phase 2: Evidence Packs (Future)

**Status**: Not started

**Planned Deliverables**:
- Evidence pack schema definition (JSON Schema or similar)
- Read-only collectors for:
  - Filesystem metadata (no content)
  - Environment variables (redacted)
  - Process listings (metadata only)
- Pack validation gates
- Pack serialization to structured format

**Constraints**:
- All collectors are read-only
- All outputs pass through redaction engine
- Explicit consent required for each data type
- No auto-discovery; sources must be explicitly listed

## Phase 3: Optional Connectors (Future)

**Status**: Not started

**Planned Deliverables**:
- Connector interface contract
- Reference implementation for local filesystem
- Connector consent model (explicit opt-in per connector)
- Connector audit logging

**Constraints**:
- Connectors are read-only
- No network connectors in initial phase
- Each connector requires explicit configuration
- No default connectors enabled

## Non-Goals (Permanent)

The following are explicitly out of scope for all phases:

| Non-Goal | Rationale |
|----------|-----------|
| Write operations | Read-only architecture |
| Network access | AirGap alignment |
| Shell execution | Security policy |
| Automated remediation | OpsPack is observation-only |
| Real-time streaming | Batch evidence packs only |
| Agent deployment | No long-running processes |

## Success Criteria

Each phase must meet:

1. All CI validations pass
2. No networking imports in production code
3. No shell execution patterns
4. Markdown hygiene compliance
5. Security review approval

## References

- [README.md](../README.md) - Product overview
- [SECURITY.md](../SECURITY.md) - Security policy
- [INTERFACE_CONTRACT.md](./INTERFACE_CONTRACT.md) - Module contracts
