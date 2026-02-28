# Run in Python shell
from app import app, db
from models import User

with app.app_context():
    # Check if admin exists
    if not User.query.filter_by(username='admin').first():
        # Create admin user
        admin = User(
            username='admin',
            email='admin@miem.hse.ru',
            full_name='Администратор системы',
            affiliation='НИУ ВШЭ, МИЭМ',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print(f"Username: {admin.username}")
        print(f"Password: admin123")
    else:
        print("Admin user already exists")