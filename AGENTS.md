# AGENTS.md - Development Guidelines for This Environment

This home directory contains scientific research files and software installations, including a Flask web application in `2Dmat/`.

## 2Dmat Flask Application

A materials science database for storing/browsing 2D materials with DFT-calculated properties.

### Project Structure

```
2Dmat/
├── app.py              # Main Flask application (routes, views)
├── models.py           # SQLAlchemy database models
├── forms.py            # WTForms form definitions
├── database.py         # Database configuration
├── utils/visualization.py  # Structure/band structure/DOS visualization
├── templates/         # Jinja2 HTML templates
├── static/             # CSS, JS, images
├── instance/          # SQLite database
└── requirements.txt    # Python dependencies
```

### Build/Run Commands

```bash
# Install dependencies
cd 2Dmat && pip install -r requirements.txt

# Initialize database
python init_db.py

# Run development server
python app.py

# Or with Flask CLI
FLASK_APP=app.py flask run --debug

# Reset database
python reset_db.py
```

### Testing Commands

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest

# Run single test
pytest tests/test_file.py::test_function_name
python -m pytest path/to/test.py::TestClass::test_method

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Style Guidelines

- Follow PEP 8 for Python
- Maximum line length: 100 characters
- Use 4 spaces for indentation
- Add docstrings to functions and classes
- Use type hints where beneficial

### Imports Order

1. Standard library (os, sys, datetime, json, etc.)
2. Third-party Flask/extension imports
3. Local application imports

```python
import os
from datetime import datetime
import json

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from models import db, User, Material
from forms import MaterialForm
```

### Error Handling

```python
# Good - specific exception handling
try:
    result = db.session.get(Model, id)
    if result is None:
        abort(404)
except ValueError as e:
    flash(f"Invalid input: {e}", "danger")
    return redirect(url_for('index'))

# Avoid bare except
```

### Key Patterns

- Routes use `@login_required` decorator for protected endpoints
- Database operations use `db.session.commit()` after modifications
- Forms validate with `form.validate_on_submit()`
- Use `flash()` for user feedback messages
- JSON fields store serialized data (use `json.loads()` / `json.dumps()`)

### Database

- SQLite by default (`instance/2dmaterials.db`)
- Uses Flask-Migrate for migrations
- Default admin: username `admin`, password `admin123`

## General Principles

1. **Readability**: Code should be easy to understand
2. **Consistency**: Follow existing patterns in the codebase
3. **Testing**: Add tests for new functionality
4. **Error Handling**: Handle errors explicitly, don't silently fail
5. **Security**: Never expose secrets, validate inputs

## Other Codebases

For other Python projects in this directory:

```bash
# Linting
flake8 . && pylint . && ruff check .

# Type checking
mypy .

# Run tests
pytest path/to/test.py::test_function
python -m unittest path.to.test_module.TestClass.test_method
```

## Before Making Changes

1. Understand the existing code structure
2. Run existing tests to ensure they pass
3. Make minimal, focused changes
4. Test changes thoroughly
5. Run linters/formatters before committing
