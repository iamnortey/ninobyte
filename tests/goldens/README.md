# Cross-Product Golden Files

This directory contains expected output (golden files) for cross-product tests.

## Structure

```
goldens/
├── common/           # Shared expected outputs
├── [product-name]/   # Product-specific goldens if needed at repo level
└── ...
```

## Usage

Individual products have their own `tests/goldens/` directories. This directory is for goldens that span multiple products or test integration scenarios.
