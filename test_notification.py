#!/usr/bin/env python
"""
Test Notification Script

This script manually tests adding notification records to the database.
For development and testing purposes only.
"""

import os
import sys
from datetime import datetime
import logging
from dotenv import load_dotenv

# Add the current directory to the path so that we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_notification')

# Load environment variables
load_dotenv()

# Import app after setting up environment
from app import app, User, Birthday, db, BirthdayNotification

def add_test_notification():
    """
    Add a test notification record for the first birthday of the first user
    """
    with app.app_context():
        # Get first user
        user = User.query.first()
        if not user:
            logger.error("No users found in the database")
            return False
        
        # Get first birthday for this user
        birthday = Birthday.query.filter_by(user_id=user.id).first()
        if not birthday:
            logger.error(f"No birthdays found for user {user.username}")
            return False
        
        # Create a notification record
        current_year = datetime.now().year
        today = datetime.now().date()
        
        notification = BirthdayNotification(
            birthday_id=birthday.id,
            user_id=user.id,
            notification_date=today,
            year_notified=current_year
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"Added test notification record for {birthday.name}'s birthday (ID: {birthday.id})")
        logger.info(f"User: {user.username} (ID: {user.id})")
        logger.info(f"Notification date: {today}, Year notified: {current_year}")
        
        return True

def main():
    """
    Main function
    """
    logger.info("Starting test notification process")
    
    success = add_test_notification()
    
    if success:
        logger.info("Test notification added successfully")
    else:
        logger.error("Failed to add test notification")
    
    logger.info("Test completed")

if __name__ == "__main__":
    main() 