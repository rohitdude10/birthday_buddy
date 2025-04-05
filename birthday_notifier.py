#!/usr/bin/env python
"""
Birthday Notification Script

This script checks for upcoming birthdays in the next 2 days and prepares to send email notifications.
Can be scheduled via cron or other task scheduler to run daily.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Add the current directory to the path so that we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('birthday_notifications.log')
    ]
)
logger = logging.getLogger('birthday_notifier')

# Load environment variables
load_dotenv()

# Import app after setting up environment
from app import app, User, Birthday, db, get_upcoming_birthdays_next_two_days, BirthdayNotification
from email_notifications import send_birthday_notifications

def format_birthdays_for_notification(upcoming_birthdays):
    """
    Format birthday data for notification purposes
    """
    notifications = []
    
    for user_id, data in upcoming_birthdays.items():
        user = data['user']
        birthdays = data['birthdays']
        
        # Get already notified birthdays for this user this year
        current_year = datetime.now().year
        already_notified = {}
        
        with app.app_context():
            notifications_sent = BirthdayNotification.query.filter_by(
                user_id=user_id, 
                year_notified=current_year
            ).all()
            
            # Create a lookup dictionary for quick checks
            for notification in notifications_sent:
                already_notified[notification.birthday_id] = True
        
        # Filter out birthdays that have already been notified
        birthdays_to_notify = []
        
        for birthday in birthdays:
            # Skip if already notified this year
            if birthday['id'] in already_notified:
                logger.info(f"Skipping notification for birthday ID {birthday['id']} - already notified this year")
                continue
                
            birthdays_to_notify.append(birthday)
        
        # Skip if no birthdays to notify after filtering
        if not birthdays_to_notify:
            logger.info(f"No new birthday notifications for user {user.username}")
            continue
        
        user_notification = {
            'user_id': user_id,
            'username': user.username,
            'email': user.email,
            'birthdays': []
        }
        
        for birthday in birthdays_to_notify:
            user_notification['birthdays'].append({
                'id': birthday['id'],
                'name': birthday['name'],
                'date': birthday['this_year_date'].strftime('%Y-%m-%d'),
                'days_until': birthday['days_until'],
                'age': birthday['age'],
                'notes': birthday['notes']
            })
        
        notifications.append(user_notification)
    
    return notifications

def record_notifications(notifications):
    """
    Record which birthday notifications were sent
    """
    current_year = datetime.now().year
    today = datetime.now().date()
    
    with app.app_context():
        for notification in notifications:
            user_id = notification['user_id']
            
            for birthday in notification['birthdays']:
                birthday_id = birthday['id']
                
                # Create a notification record
                notification_record = BirthdayNotification(
                    birthday_id=birthday_id,
                    user_id=user_id,
                    notification_date=today,
                    year_notified=current_year
                )
                
                db.session.add(notification_record)
            
        # Commit all changes at once
        db.session.commit()
    
    logger.info("Notification records saved to database")

def process_notifications(notifications):
    """
    Process notifications and log summary
    """
    logger.info(f"Found {len(notifications)} users with upcoming birthdays")
    
    for notification in notifications:
        user_email = notification['email']
        username = notification['username']
        birthdays = notification['birthdays']
        
        logger.info(f"User: {username} ({user_email}) has {len(birthdays)} upcoming birthdays")
        
        for birthday in birthdays:
            name = birthday['name']
            date = birthday['date']
            days_until = birthday['days_until']
            age = birthday['age']
            
            if days_until == 0:
                logger.info(f"TODAY: {name}'s birthday is today! They are turning {age}.")
            else:
                logger.info(f"SOON: {name}'s birthday is in {days_until} days on {date}. They will be {age}.")
    
    # Return notifications for further processing
    return notifications

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Birthday notification script')
    parser.add_argument('--send-emails', action='store_true', 
                        help='Actually send email notifications (default: just log)')
    parser.add_argument('--force', action='store_true',
                        help='Force sending notifications even if already sent')
    return parser.parse_args()

def main():
    """
    Main function to run the birthday notification process
    """
    args = parse_arguments()
    
    logger.info("Starting birthday notification check")
    logger.info(f"Email sending is {'ENABLED' if args.send_emails else 'DISABLED'}")
    
    with app.app_context():
        # Get upcoming birthdays for the next 2 days
        upcoming_birthdays = get_upcoming_birthdays_next_two_days()
        
        if not upcoming_birthdays:
            logger.info("No upcoming birthdays in the next 2 days")
            return
        
        # Format birthdays for notification, filtering already notified ones
        notifications = format_birthdays_for_notification(upcoming_birthdays)
        
        # If forcing notifications, bypass the filtering
        if args.force and not notifications:
            logger.info("Force option enabled - preparing notifications without filtering")
            notifications = []
            
            for user_id, data in upcoming_birthdays.items():
                user = data['user']
                birthdays = data['birthdays']
                
                user_notification = {
                    'user_id': user_id,
                    'username': user.username,
                    'email': user.email,
                    'birthdays': []
                }
                
                for birthday in birthdays:
                    user_notification['birthdays'].append({
                        'id': birthday['id'],
                        'name': birthday['name'],
                        'date': birthday['this_year_date'].strftime('%Y-%m-%d'),
                        'days_until': birthday['days_until'],
                        'age': birthday['age'],
                        'notes': birthday['notes']
                    })
                
                if user_notification['birthdays']:
                    notifications.append(user_notification)
        
        if not notifications:
            logger.info("No new birthday notifications to send")
            return
        
        # Process notifications (log info)
        processed_notifications = process_notifications(notifications)
        
        # Send email notifications if enabled
        if args.send_emails:
            logger.info("Sending email notifications...")
            sent = send_birthday_notifications(processed_notifications)
            if sent:
                logger.info("Email notifications sent successfully")
                # Record which notifications were sent
                record_notifications(processed_notifications)
            else:
                logger.error("Failed to send email notifications")
        else:
            logger.info("Email notifications prepared but not sent (email sending is disabled)")
            logger.info("Use --send-emails flag to enable sending")
    
    logger.info("Birthday notification check completed")

if __name__ == "__main__":
    main() 