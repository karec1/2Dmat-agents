# init_db.py
from app import app, db
from models import User, Material, Verification, Comment, Bookmark

def init_database():
    with app.app_context():
        # Drop all tables (if they exist)
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating tables...")
        db.create_all()
        
        # Create admin user
        print("Creating admin user...")
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
        
        print("Database initialized successfully!")
        print(f"Admin username: {admin.username}")
        print(f"Admin password: admin123")

if __name__ == '__main__':
    init_database()