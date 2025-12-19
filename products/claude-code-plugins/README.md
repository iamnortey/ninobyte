# Claude Code Plugins

This directory contains Claude Code plugin implementations.

## Status

No plugins released yet. Planned for future versions.

## Structure

Each plugin will be a subdirectory:
```
claude-code-plugins/
├── [plugin-name]/
│   ├── README.md
│   ├── src/
│   ├── tests/
│   └── ...
└── ...
```

## Development Guidelines

- Follow [THREAT_MODEL.md](../../docs/architecture/THREAT_MODEL.md) security requirements
- Validate against official Claude Code plugin specification (see VALIDATION_LOG.md)
- Include comprehensive test fixtures
