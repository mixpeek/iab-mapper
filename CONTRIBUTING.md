## Contributing

1. Fork and create a feature branch.
2. Setup dev env: `python -m venv .venv && source .venv/bin/activate && pip install -e .[emb] && pip install -r requirements-dev.txt || pip install pytest`
3. Run tests: `pytest -q`
4. Open a PR with a concise description and screenshots/logs if helpful.

### Commit style
Use conventional commits where possible: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`.

### Reporting issues
Please include reproduction steps, expected vs actual behavior, and environment details.

