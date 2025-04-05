import os
import pymysql
from app import app, db, User, Birthday
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Resetting database...")

timeout = 10

# Connect to MySQL database
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="birthday_buddy",
    host=os.environ.get('DATABASE_URI'),
    password=os.environ.get('PASSWORD'),
    read_timeout=timeout,
    port=26323,
    user="avnadmin",
    write_timeout=timeout,
)

# Create the tables fresh with the new schema
print("Creating new database with updated schema...")
with app.app_context():
    # Drop all existing tables
    try:
        db.drop_all()
        print("Existing tables dropped.")
    except Exception as e:
        print(f"Error dropping tables: {e}")
    
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")

print("\nDatabase has been reset. You can now run the application with the new schema.")
print("You'll need to create a new user account to get started.") 