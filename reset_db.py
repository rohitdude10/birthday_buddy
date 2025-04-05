import os
import pymysql
from app import app, db, User, Birthday
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Resetting database...")

# Get environment variables
db_name = os.environ.get('DB_NAME')
host_uri = os.environ.get('DATABASE_URI').split('@')[1].split('/')[0]
password = os.environ.get('PASSWORD')
username = os.environ.get('USERNAME')

# Connect to MySQL database
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=10,
    cursorclass=pymysql.cursors.DictCursor,
    db=db_name,
    host=host_uri.split(':')[0],
    password=password,
    read_timeout=10,
    port=int(host_uri.split(':')[1]),
    user=username,
    write_timeout=10,
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