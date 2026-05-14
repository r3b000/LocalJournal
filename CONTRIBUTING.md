# Contributing to LocalJournal

Thank you for your interest in contributing to LocalJournal.

LocalJournal uses a **maintainer-approved contribution model**. The repository is public so anyone can view it, clone it, and fork it, but changes to the official project are reviewed and accepted only when they align with the maintainer's direction.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Approval Policy](#approval-policy)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Development Tips](#development-tips)
- [Questions](#questions)
- [License](#license)

***

## Code of Conduct

### Our Standards

- Be respectful and inclusive.
- Accept constructive criticism professionally.
- Focus on what improves the project.
- Show patience and empathy in discussion.

### Unacceptable Behavior

- Harassment, discrimination, or abusive language.
- Trolling, hostility, or repeated bad-faith arguments.
- Publishing another person's private information without permission.
- Any conduct that would reasonably make collaboration unsafe or unproductive.

***

## How to Contribute

### Report Bugs

Bug reports are welcome.

Before opening a new issue, check existing issues to avoid duplicates.

A good bug report should include:

- A clear and descriptive title.
- Steps to reproduce the issue.
- Expected behavior and actual behavior.
- Screenshots, logs, or error messages when relevant.
- Environment details, including OS version, Python version, and LocalJournal version.

### Suggest Enhancements

Enhancement ideas are also welcome through issues.

A good enhancement request should include:

- A clear and descriptive title.
- A detailed description of the idea.
- Why the change would be useful.
- A possible implementation direction, if you have one.

### Code Contributions

Code contributions are **not** accepted as open, unsolicited pull requests.

If you want to contribute code to the official repository, start by opening an issue or contacting the maintainer for approval first.

***

## Approval Policy

### What does not require approval

You may do the following without asking first:

- Clone the repository for personal use.
- Fork the repository for private experimentation.
- Open issues for bugs, questions, or enhancement ideas.
- Review the code and documentation for learning purposes.

### What requires approval first

You must get maintainer approval before:

- Opening a pull request intended for the official repository.
- Starting feature work for the official roadmap.
- Requesting collaborator or write access.
- Making changes that affect database structure, migrations, backups, data storage paths, or release workflow.

### Why this policy exists

LocalJournal is maintained with a specific product direction, release flow, and data-safety model. Approval-first contributions help keep the project consistent, easier to review, and safer for users who depend on local data handling.

***

## Development Setup

### Prerequisites

- Python
- Git
- A virtual environment tool

### Setup Steps

**1. Clone the repository**

```bash
git clone https://github.com/YOUR-USERNAME/LocalJournal.git
cd LocalJournal
```

**2. Create a virtual environment**

```bash
python -m venv .venv
```

**3. Activate the virtual environment**

On Windows CMD:

```bat
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

**4. Install dependencies**

```bash
pip install -r requirements.txt
```

**5. Run the application**

```bash
streamlit run app.py
```

### Project Structure

```text
LocalJournal/
├── app.py
├── runapp.py
├── components/
├── config/
├── database/
├── databasemigrations/
├── Pages/
├── utils/
├── assets/
└── icons/
```

***

## Coding Standards

### Python Style Guide

- Follow PEP 8.
- Use clear variable and function names.
- Keep changes focused and readable.
- Use type hints where they improve clarity.
- Write docstrings for important functions and classes.
- Avoid unrelated refactors in the same pull request.

### Database Work

- Use parameterized queries.
- Use proper error handling.
- Use context managers for database connections.
- Add logging where operational changes matter.
- Test schema and migration changes on a copy of production data.

### UI and App Structure

- Reuse existing components where possible.
- Keep naming consistent with the current project layout.
- Validate user input before saving or processing data.
- Preserve LocalJournal's local-first and privacy-first behavior.

***

## Commit Guidelines

### Preferred Format

```text
type(scope): subject
```

### Common Types

| Type | Use for |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Internal code restructuring |
| `test` | Adding or updating tests |
| `chore` | Maintenance work |

### Examples

```text
feat(trades): add partial-close validation
```

```text
fix(statistics): correct equity curve null handling
```

```text
docs(readme): clarify local-only data storage
```

***

## Pull Request Process

### Before Opening a Pull Request

1. Get maintainer approval first.
2. Make sure the work matches the agreed scope.
3. Test the change locally.
4. Update documentation when needed.
5. Update `CHANGELOG.md` when the change affects users or releases.

### Approved Contribution Flow

1. Open or reference the issue that was approved.
2. Create a branch from the latest `main`.
3. Make focused commits.
4. Test thoroughly.
5. Open the pull request with a clear description.

### Pull Request Expectations

An approved pull request should include:

- A short explanation of the change.
- Why the change is needed.
- Testing notes.
- Documentation updates, if any.
- Migration or release impact, if any.

### Review Process

- The maintainer reviews all official pull requests.
- Feedback and discussion must be resolved before merge.
- Approval does not guarantee merge if the implementation changes scope or quality expectations.
- Unapproved pull requests may be closed or declined.

***

## Development Tips

### Testing Your Changes

```bash
python testlocaljournalcomprehensive.py
streamlit run app.py
```

### Database Changes

If you modify database behavior:

1. Update the relevant files in `database/`.
2. Add or update the migration script in `databasemigrations/` when required.
3. Test the migration on a copy of the database.
4. Document the change in `CHANGELOG.md`.

### Adding New Pages

1. Follow the existing structure inside `Pages/`.
2. Reuse components from `components/` where possible.
3. Handle empty states, validation, and errors cleanly.
4. Test with realistic account and trade data.

***

## Questions

For contribution questions:

1. Check the existing documentation.
2. Search existing issues.
3. Open a new issue if the answer is not already available.

***

## License

By contributing approved changes to LocalJournal, you agree that your contributions will be licensed under the project's license.

***

*Thank you for supporting LocalJournal.*