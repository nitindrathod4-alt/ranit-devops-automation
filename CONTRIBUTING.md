# Contributing to RANIT

Thanks for helping improve RANIT.

## Development setup

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Guidelines
- Keep changes small, tested, and documented.
- Never include secrets, customer data, AWS credentials, tokens, or private keys.
- Prefer read-only behavior by default.
- Future command execution must include timeouts, explicit target selection, dry-run support, and safe failure behavior.
- Cloud changes must use least privilege and require confirmation for destructive or production actions.
- Update docs and tests when behavior changes.

## Pull requests
Explain the problem, the approach, tests run, and any security or cost implications.
