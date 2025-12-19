# MCP Servers

This directory contains Model Context Protocol (MCP) server implementations.

## Status

No MCP servers released yet. Planned for future versions.

## Structure

Each MCP server will be a subdirectory:
```
mcp-servers/
├── [server-name]/
│   ├── README.md
│   ├── src/
│   ├── tests/
│   └── ...
└── ...
```

## Development Guidelines

- Follow [THREAT_MODEL.md](../../docs/architecture/THREAT_MODEL.md) security requirements
- Validate against official MCP specification (see VALIDATION_LOG.md)
- Include comprehensive test fixtures
