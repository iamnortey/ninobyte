#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "Ninobyte Closeout Validation"
echo "============================================================"
echo

python3 scripts/ci/validate_validation_log_links.py
python3 scripts/ci/validate_adr_links.py
python3 scripts/ops/build_evidence_index.py --check
python3 scripts/ops/test_evidence_index_determinism.py
python3 scripts/ops/evidence_contract_check.py
python3 scripts/ci/validate_artifacts.py
python3 -m pytest -q

echo
echo "============================================================"
echo "✅ All closeout validations PASSED"
echo "============================================================"
