# Run in Python shell
from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('admin123')  # Reset to default
        db.session.commit()
        print("Admin password reset to: admin123")
    else:
        print("Admin user not found!")