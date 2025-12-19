# Cross-Product Test Fixtures

This directory contains test fixtures shared across multiple products.

## Structure

```
fixtures/
├── common/           # Shared test inputs
├── [product-name]/   # Product-specific fixtures if needed at repo level
└── ...
```

## Usage

Individual products have their own `tests/fixtures/` directories. This directory is for fixtures that span multiple products or test integration scenarios.
