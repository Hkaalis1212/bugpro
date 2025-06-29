# Contributing to Bug Reporting System

Thank you for your interest in contributing to our AI-powered bug reporting system! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Git

### Local Development
1. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/bug-reporting-system.git
   cd bug-reporting-system
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## Code Style Guidelines

### Python Code
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### HTML/CSS
- Use semantic HTML elements
- Follow TailwindCSS utility-first approach
- Ensure responsive design for mobile devices
- Maintain dark theme consistency

### JavaScript
- Use modern ES6+ features
- Keep functions pure when possible
- Add comments for complex logic
- Follow consistent naming conventions

## Testing

### Running Tests
Before submitting a pull request, run the full test suite:

```bash
# Run unit tests
python comprehensive_tests.py

# Run integration tests
python integration_test.py

# Run security tests
python -m pytest security_tests.py
```

### Writing Tests
- Add tests for all new functionality
- Ensure tests are isolated and independent
- Mock external services (Stripe, OpenAI, GitHub)
- Test both success and failure scenarios

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**:
   ```bash
   python comprehensive_tests.py
   ```

4. **Commit your changes**:
   ```bash
   git commit -m "Add: Brief description of your change"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a pull request**:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots for UI changes

## Commit Message Guidelines

Use clear, descriptive commit messages:

- `Add: New feature or functionality`
- `Fix: Bug fixes`
- `Update: Changes to existing features`
- `Docs: Documentation updates`
- `Test: Adding or updating tests`
- `Refactor: Code restructuring without feature changes`

## Feature Requests

When proposing new features:

1. Check existing issues to avoid duplicates
2. Describe the problem you're solving
3. Provide detailed requirements
4. Consider backward compatibility
5. Include mockups or examples if applicable

## Bug Reports

When reporting bugs:

1. Use the application's built-in bug reporting feature
2. Provide steps to reproduce
3. Include environment details
4. Add screenshots or recordings if helpful
5. Specify expected vs actual behavior

## Security Issues

For security vulnerabilities:

1. **Do not** create public issues
2. Email security concerns privately
3. Provide detailed reproduction steps
4. Allow time for patches before disclosure

## Code Review Process

All submissions require review:

- Maintainers will review for code quality
- Tests must pass
- Documentation must be updated
- Changes should not break existing functionality

## Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Bug fixes and stability improvements
- Performance optimizations
- Security enhancements
- Test coverage improvements

### Medium Priority
- New AI analysis features
- Enhanced GitHub integration
- Additional export formats
- Mobile experience improvements

### Low Priority
- UI/UX enhancements
- Documentation improvements
- Code refactoring
- Additional integrations

## Development Environment

### Database Setup
The application uses PostgreSQL. For development:

```sql
CREATE DATABASE bugtracker_dev;
CREATE USER bugtracker WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE bugtracker_dev TO bugtracker;
```

### Environment Variables
Required environment variables:

```
DATABASE_URL=postgresql://bugtracker:password@localhost/bugtracker_dev
SESSION_SECRET=your-development-secret
OPENAI_API_KEY=your-openai-key
STRIPE_SECRET_KEY=sk_test_...
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues
3. Create a new issue with the "question" label
4. Join our community discussions

Thank you for contributing to make bug reporting better for everyone!