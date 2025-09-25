# Contributing to IAB Mapper

Thank you for your interest in contributing to the IAB Mapper! This project helps the industry migrate from IAB Content Taxonomy 2.x to 3.0, and we welcome contributions from the community.

## 🚀 Getting Started

### Development Setup

1. **Fork and clone** the repository
   ```bash
   git clone https://github.com/your-username/iab-mapper.git
   cd iab-mapper
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Basic installation
   pip install -e .
   
   # With embeddings support
   pip install -e ".[emb]"
   
   # Development dependencies
   pip install -r requirements-dev.txt
   ```

4. **Run tests** to ensure everything works
   ```bash
   pytest -q
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Types of Contributions

### Bug Reports
- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include reproduction steps, expected vs actual behavior, and environment details
- Provide sample data if possible (anonymized)

### Feature Requests
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- Explain the use case and expected behavior
- Consider if the feature aligns with the project's scope

### Code Contributions
- **Small fixes:** Direct PRs are welcome
- **Larger features:** Open an issue first to discuss the approach
- **Documentation:** Always welcome improvements to README, docstrings, or examples

## 🔧 Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings for new functions/classes
- Keep functions focused and testable

### Commit Style
Use conventional commits where possible:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `chore:` Maintenance tasks
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements

### Testing
- Add tests for new functionality
- Ensure existing tests pass: `pytest -q`
- Test with sample data from the `demo/` directory
- Consider edge cases and error conditions

### Pull Request Process

1. **Update documentation** if you change functionality
2. **Add tests** for new features
3. **Update CHANGELOG.md** with your changes
4. **Ensure all tests pass**
5. **Request review** from maintainers

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Tested with sample data

## Screenshots/Logs
If applicable, add screenshots or logs showing the changes.
```

## 🧪 Testing with Sample Data

The repository includes sample data in the `demo/` directory:
- `sample_2x_codes.csv` - Small test dataset
- `sample_2x_codes_large.csv` - Larger test dataset
- `sample_2x_codes.json` - JSON format examples

Test your changes with:
```bash
# Test with small dataset
iab-mapper demo/sample_2x_codes.csv -o test_output.json

# Test with larger dataset
iab-mapper demo/sample_2x_codes_large.csv -o test_output_large.json
```

## 📊 Performance Considerations

- The mapper processes data locally, so performance matters
- Consider memory usage with large datasets
- Embeddings can be memory-intensive - test with realistic data sizes
- Profile changes that might affect processing speed

## 🔒 Security & Privacy

- This tool processes data locally - no external APIs by default
- Be mindful of any changes that might introduce external dependencies
- Ensure PII handling remains local-only
- Test offline functionality

## 📞 Getting Help

- **Issues:** [GitHub Issues](https://github.com/mixpeek/iab-mapper/issues)
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** Check the [README](README.md) and inline docs

## 🎯 Project Goals

The IAB Mapper aims to:
- Simplify IAB 2.x → 3.0 migration for the industry
- Provide reliable, auditable mapping results
- Support local-first processing for privacy
- Enable extensibility through custom synonyms and overrides

When contributing, keep these goals in mind and consider how your changes support the broader industry adoption of IAB 3.0.

---

Thank you for contributing to the IAB Mapper! 🚀

