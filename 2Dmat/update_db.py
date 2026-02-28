# Stop your Flask app and run this in a Python shell:
from app import app, db
from models import User

with app.app_context():
    # This will add the new column if it doesn't exist
    # For SQLite, you might need to recreate the table or use migrations
    # Quick workaround: delete your database file and let Flask recreate it
    # Or use Flask-Migrate for proper migrations
    
    # For development, you can just delete 2dmaterials.db and restart
    pass