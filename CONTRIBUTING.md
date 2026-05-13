# Contributing to LocalJournal

Thank you for your interest in contributing to LocalJournal! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or insulting/derogatory comments
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**Bug Report Should Include:**
- Clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Screenshots or error messages if applicable
- Environment details:
  - OS version
  - Python version
  - LocalJournal version

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.

**Enhancement Suggestion Should Include:**
- Clear and descriptive title
- Detailed description of the proposed feature
- Explanation of why this enhancement would be useful
- Possible implementation approach (optional)

### Code Contributions

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment tool

### Setup Steps

**1. Clone your fork**
```bash
git clone https://github.com/YOUR-USERNAME/LocalJournal.git
cd LocalJournal
```

**2. Create virtual environment**
```bash
py -3.11 -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the application**
```bash
streamlit run app.py
```

### Project Structure

```
LocalJournal/
├── app.py              # Main entry point
├── components/         # Reusable UI components
├── config/             # Configuration and constants
├── database/           # Database operations
├── pages/              # Streamlit pages
└── utils/              # Utility functions
```

---

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use meaningful variable and function names
- Maximum line length: **100 characters**
- Use type hints where appropriate
- Write docstrings for functions and classes

**Example:**
```python
def calculate_position_size(
    account_equity: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss: float,
    direction: str
) -> float:
    """
    Calculate position size based on risk parameters.

    Args:
        account_equity: Total account equity
        risk_percentage: Risk percentage per trade
        entry_price: Entry price for the trade
        stop_loss: Stop loss price
        direction: Trade direction ('LONG' or 'SHORT')

    Returns:
        Position size in units
    """
    # Implementation
    pass
```

### Database Operations

- Use parameterized queries to prevent SQL injection
- Implement proper error handling
- Use context managers for database connections
- Add logging for important operations

### UI Components

- Keep components modular and reusable
- Use consistent naming conventions
- Add helpful placeholder text and tooltips
- Validate user inputs before processing

---

## Commit Guidelines

### Commit Message Format

```
type(scope): subject

body

footer
```

### Types

| Type | Description |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, no logic change) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

### Examples

```
feat(trades): add multi-exit support for partial closes

Implement functionality to handle multiple exit prices and
allocations for scaling out of positions.

Closes #42
```

```
fix(database): correct equity calculation in statistics query

The equity curve was calculating cumulative PnL incorrectly
when trades had NULL values. Added COALESCE to handle nulls.

Fixes #38
```

---

## Pull Request Process

### Before Submitting

1. Ensure your code follows the coding standards
2. Update documentation if needed
3. Add or update tests for your changes
4. Test thoroughly on your local machine
5. Update `CHANGELOG.md` with your changes

### Pull Request Template

```markdown
## Description
Clear description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran and their results.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated and passing
```

### Review Process

1. At least one maintainer must review the PR
2. All discussions must be resolved
3. All CI checks must pass
4. Maintainer will merge when approved

---

## Development Tips

### Testing Your Changes

```bash
# Run the test suite
python test_localjournal_comprehensive.py

# Test specific functionality
streamlit run app.py
```

### Database Changes

If you modify the database schema:
1. Update `database/schema.py`
2. Create migration script in `database/migrations/`
3. Test migration on a **copy** of the production database
4. Document the changes in `CHANGELOG.md`

### Adding New Pages

1. Create file in `pages/` directory: `X_PageName.py`
2. Follow existing page structure
3. Use reusable components from `components/`
4. Add appropriate error handling
5. Test with different account states

---

## Questions?

If you have questions about contributing, please:
1. Check existing documentation
2. Search through issues
3. Open a new issue with the `question` label

---

## License

By contributing to LocalJournal, you agree that your contributions will be licensed under the **MIT License**.

---

*Thank you for contributing to LocalJournal! Your efforts help make this project better for everyone.* 🙏
