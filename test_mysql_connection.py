import pymysql
from app import app, db, User, Birthday
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test the MySQL connection and database configuration"""
    print("Testing MySQL connection...")
    
    # Get environment variables
    db_name = os.environ.get('DB_NAME')
    host_uri = os.environ.get('DATABASE_URI').split('@')[1].split('/')[0]
    password = os.environ.get('PASSWORD')
    username = os.environ.get('USERNAME')
    
    # Try direct connection
    try:
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
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("Direct connection successful!")
        connection.close()
    except Exception as e:
        print(f"Direct connection error: {e}")
    
    # Try SQLAlchemy connection via the Flask app
    print("\nTesting SQLAlchemy connection through Flask...")
    with app.app_context():
        try:
            # Test if we can query users
            user_count = User.query.count()
            print(f"Connection successful! Found {user_count} users in the database.")
            
            # Test if birthday table exists
            birthday_count = Birthday.query.count()
            print(f"Found {birthday_count} birthdays in the database.")
        except Exception as e:
            print(f"SQLAlchemy connection error: {e}")
    
    print("\nDatabase testing complete.")

if __name__ == "__main__":
    test_connection() 