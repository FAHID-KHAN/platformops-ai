# Contributing

Thank you for helping build PlatformOps AI.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Keep the first release read-only, fixture-testable, and independent of private infrastructure. New integrations should return typed evidence and include fake or fixture providers before requiring a real external system.

## Pull Requests

- Include focused tests for behavior changes.
- Do not commit kubeconfigs, tokens, private hostnames, `.env` files, or sensitive logs.
- Keep provider credentials separate from model credentials.
- Document new public capabilities and risk levels.

