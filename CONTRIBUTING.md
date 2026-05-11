# Contributing to EduSence AI

Thank you for your interest in contributing to EduSence AI! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Relevant logs or screenshots

### Suggesting Enhancements

For feature requests:
- Describe the feature and its benefits
- Provide use cases
- Suggest implementation approach if possible

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed
4. **Test your changes**
   - Ensure existing tests pass
   - Add new tests for new features
5. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of changes"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**
   - Provide clear description
   - Reference related issues
   - Include screenshots/videos if applicable

## 📝 Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions and classes
- Keep functions focused and small
- Comment complex algorithms

## 🧪 Testing

- Test on both CPU and GPU if possible
- Test with different video sources (webcam, video files)
- Verify all presets work correctly
- Check post-processing utilities

## 📚 Documentation

- Update README.md for user-facing changes
- Update relevant documentation files
- Add inline comments for complex code
- Include examples for new features

## 🎯 Areas for Contribution

### High Priority
- Performance optimization
- GPU acceleration improvements
- Memory usage optimization
- Better error handling

### Medium Priority
- Additional configuration presets
- Improved clustering algorithms
- Better quality metrics
- Multi-camera support

### Nice to Have
- Web dashboard
- API endpoints
- Docker support
- CI/CD pipeline
- Unit tests

## 💡 Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/EduSence-ai.git
cd EduSence-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## 🔍 Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be acknowledged

## 📜 Commit Message Guidelines

Use clear, descriptive commit messages:

- `Add: new feature or functionality`
- `Fix: bug fix`
- `Update: changes to existing feature`
- `Refactor: code restructuring`
- `Docs: documentation changes`
- `Test: test additions or changes`
- `Style: formatting, missing semicolons, etc.`

Example:
```
Add: hybrid matching with spatial proximity

- Implement spatial distance calculation
- Add spatial weight to matching score
- Update configuration with spatial weight parameter
```

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in the README

## 📞 Questions?

- Open a discussion on GitHub
- Check existing issues and documentation
- Reach out to maintainers

Thank you for contributing to EduSence AI! 🎓
