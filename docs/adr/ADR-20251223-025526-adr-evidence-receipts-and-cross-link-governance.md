# ADR-20251223-025526-adr-evidence-receipts-and-cross-link-governance: ADR evidence receipts and cross-link governance

## Status

**Status**: accepted

**Date**: 2025-12-23

## Context

Architecture decisions need immutable evidence trails like PR merges and validations. Without receipts, decisions can be altered or disputed without audit trail.

## Decision

Implement ADR governance with canonical JSON receipts and mandatory cross-link validation. Each ADR must reference exactly one decision receipt, and each receipt must be referenced by an ADR.

## Consequences

All architecture decisions have cryptographic integrity proofs. CI enforces cross-link policy preventing orphan receipts or undocumented decisions.

## Evidence Receipt

**Receipt Path**: `ops/evidence/decisions/decision_20251223_025526_7328a31.canonical.json`

This ADR is anchored to an immutable evidence receipt containing:
- Timestamp: 2025-12-23T02:55:26Z
- Git commit SHA (at time of decision)
- Decision metadata
- Cryptographic integrity proof (SHA256)
