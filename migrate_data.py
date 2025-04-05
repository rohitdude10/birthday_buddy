import pymysql
import os
from app import app, db, User, Birthday
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from sqlalchemy import inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Starting data migration for MySQL database...")

# Get environment variables
db_name = os.environ.get('DB_NAME')
host_uri = os.environ.get('DATABASE_URI')
password = os.environ.get('PASSWORD')
username = os.environ.get('USERNAME')
db_port = os.environ.get('DB_PORT', "26323")

# Setup MySQL connection
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=10,
    cursorclass=pymysql.cursors.DictCursor,
    db=db_name,
    host=host_uri,
    password=password,
    read_timeout=10,
    port=db_port,
    user=username,
    write_timeout=10,
)

with app.app_context():
    # Check if tables exist in the database
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'user' not in tables or 'birthday' not in tables:
        print("Required tables don't exist yet. Please run the application first to create tables.")
        exit(0)
    
    # Check if we already have the user table and user_id column in birthday table
    try:
        # Try to count users
        user_count = User.query.count()
        print(f"Found {user_count} users in the database.")
        
        # Check if there are birthdays without a user_id
        orphan_birthdays = Birthday.query.filter_by(user_id=None).count()
        print(f"Found {orphan_birthdays} birthdays without a user_id.")
        
        if orphan_birthdays > 0:
            # Create a default admin user if needed
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Creating default admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    created_at=datetime.utcnow()
                )
                admin_user.set_password('password123')  # Default password, should be changed
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user created with username 'admin' and password 'password123'")
            
            # Assign orphaned birthdays to the admin user
            print(f"Assigning {orphan_birthdays} birthdays to admin user...")
            for birthday in Birthday.query.filter_by(user_id=None).all():
                birthday.user_id = admin_user.id
            
            db.session.commit()
            print("Done! All birthdays have been assigned to the admin user.")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        print("You may need to run reset_db.py to reset the database with the new schema.")

print("\nMigration complete. You can now run the application with the new schema.")
print("If you created a default admin user, remember to change the password after login!") 