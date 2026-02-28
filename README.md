# 2D Materials Database

A Flask web application for storing, browsing, and managing 2D materials with DFT-calculated properties.

## Features

- Browse and search 2D materials database
- Material detail pages with structure visualization
- Band structure and DOS plots
- User authentication and profiles
- Expert verification system
- Comments and ratings
- Bookmark materials
- REST API
- CSV export

## Installation

```bash
cd 2Dmat
pip install -r requirements.txt
python init_db.py
```

## Running

```bash
python app.py
```

Or with Flask CLI:

```bash
FLASK_APP=app.py flask run --debug
```

The app runs at `http://localhost:5000`

## Default Admin

- Username: `admin`
- Password: `admin123`

## Project Structure

```
2Dmat/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy models
├── forms.py            # WTForms
├── database.py         # DB config
├── utils/
│   └── visualization.py  # Structure/DOS/Band plots
├── templates/          # Jinja2 templates
├── static/             # CSS, JS, uploads
└── instance/           # SQLite database
```

## Tech Stack

- Flask 3.0
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Matplotlib/Plotly (visualization)
- ASE (atomic structure)
