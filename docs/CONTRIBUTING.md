# Contributing to Auto Poster

## Development Setup

1. Install pre-commit hooks:
```bash
npm install
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

2. Set up backend development environment:
```bash
cd backend
poetry install --with dev,postgres
```

3. Set up frontend development environment:
```bash
cd frontend
npm install
```

## Code Quality

### Python Backend

- **Formatter:** Black (line length: 100)
- **Import Sorter:** isort
- **Linter:** Flake8

Run manually:
```bash
cd backend
black .
isort .
flake8 .
```

### TypeScript Frontend

- **Formatter:** Prettier

Run manually:
```bash
cd frontend
npm run format
```

### Pre-commit Hooks

All code quality tools run automatically via pre-commit hooks. If hooks fail:
1. Review the errors
2. Fix the issues (or let the hooks auto-fix them)
3. Stage the changes
4. Commit again

## Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat:** New feature (triggers minor version bump)
- **fix:** Bug fix (triggers patch version bump)
- **perf:** Performance improvement (triggers patch version bump)
- **refactor:** Code refactoring (triggers patch version bump)
- **docs:** Documentation only changes
- **style:** Code style changes (formatting, missing semicolons, etc)
- **test:** Adding or updating tests
- **build:** Changes to build system or dependencies
- **ci:** Changes to CI/CD configuration
- **chore:** Other changes that don't modify src or test files
- **revert:** Reverts a previous commit

### Examples

```
feat(instagram): add support for carousel posts

fix(video): resolve audio sync issue in generated videos

docs: update YouTube API setup instructions

refactor(database): optimize post query performance
```

### Scope

Optional but recommended. Examples: `instagram`, `youtube`, `video`, `database`, `api`, `ui`

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the footer:

```
feat(api): change post creation endpoint

BREAKING CHANGE: POST /api/posts now requires platform selection
```

## Pull Request Process

1. Create a feature branch from `dev`
2. Make your changes following the code quality guidelines
3. Ensure all tests pass
4. Commit using conventional commit format
5. Push to your branch
6. Open a Pull Request to `dev` branch

## Release Process

Releases are automated via semantic-release:

1. Merge PRs to `dev` branch for development releases (e.g., `1.2.0-dev.1`)
2. Merge `dev` to `main` for production releases (e.g., `1.2.0`)
3. GitHub Actions will:
   - Analyze commits
   - Determine version bump
   - Generate changelog
   - Create GitHub release
   - Build and push Docker images to GHCR

Version bumps:
- `feat:` → Minor version (1.0.0 → 1.1.0)
- `fix:`, `perf:`, `refactor:` → Patch version (1.0.0 → 1.0.1)
- `BREAKING CHANGE:` → Major version (1.0.0 → 2.0.0)

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## License

By contributing, you agree that your contributions will be licensed under the project's license.
