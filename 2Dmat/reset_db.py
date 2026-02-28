# save as reset_db.py in your project folder
from app import app, db, User, Material
import os

with app.app_context():
    # Find the database file
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print("="*60)
    print("DATABASE RESET SCRIPT")
    print("="*60)
    
    # Backup warning
    if os.path.exists(db_path):
        import datetime
        backup_name = f"{db_path}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_name)
        print(f"⚠️  Backup created: {backup_name}")
        print(f"📊 Original size: {os.path.getsize(db_path)} bytes")
    else:
        print("📁 No existing database found, creating fresh")
    
    # Drop all tables
    print("🗑️  Dropping all tables...")
    db.drop_all()
    
    # Create all tables from current models
    print("🔄 Creating tables from models...")
    db.create_all()
    
    # Optional: Create default admin user if needed
    try:
        admin = User(username='admin', email='admin@example.com')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user")
    except Exception:
        db.session.rollback()
        print("Admin user already exists or model doesn't have email field")
    
    print("✅ Database reset complete!")
    print(f"📁 New database size: {os.path.getsize(db_path) if os.path.exists(db_path) else 0} bytes")
