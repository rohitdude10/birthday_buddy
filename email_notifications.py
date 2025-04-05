"""
Email Notification Module

This module handles sending email notifications for birthday reminders.
It's separate from the main application to allow for easy integration
with the notification script.
"""

import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime
import requests
import json

logger = logging.getLogger('email_notifications')

def format_birthday_email(username, birthdays):
    """
    Format the email content for upcoming birthdays
    """
    today = datetime.now().date()
    today_birthdays = [b for b in birthdays if b['days_until'] == 0]
    upcoming_birthdays = [b for b in birthdays if b['days_until'] > 0]
    
    # Create HTML content for the email
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #5e72e4; text-align: center; }}
            .birthday {{ background-color: #f8f9fa; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
            .birthday-today {{ background-color: #fff3cd; }}
            .header {{ font-weight: bold; margin-bottom: 5px; }}
            .notes {{ font-style: italic; color: #6c757d; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Birthday Reminders</h1>
            <p>Hello {username},</p>
    """
    
    if today_birthdays:
        html += f"""
            <p>You have <strong>{len(today_birthdays)}</strong> birthdays today!</p>
            
            <h2>Today's Birthdays</h2>
        """
        
        for birthday in today_birthdays:
            html += f"""
            <div class="birthday birthday-today">
                <div class="header">{birthday['name']} (turns {birthday['age']} today)</div>
                <div>Date: {birthday['date']}</div>
            """
            
            if birthday['notes']:
                html += f"""<div class="notes">Notes: {birthday['notes']}</div>"""
                
            html += """</div>"""
    
    if upcoming_birthdays:
        html += f"""
            <h2>Upcoming Birthdays (Next 2 Days)</h2>
        """
        
        for birthday in upcoming_birthdays:
            day_text = "day" if birthday['days_until'] == 1 else "days"
            html += f"""
            <div class="birthday">
                <div class="header">{birthday['name']} (turns {birthday['age']} in {birthday['days_until']} {day_text})</div>
                <div>Date: {birthday['date']}</div>
            """
            
            if birthday['notes']:
                html += f"""<div class="notes">Notes: {birthday['notes']}</div>"""
                
            html += """</div>"""
    
    html += """
            <div class="footer">
                <p>This is an automated message from your Birthday Reminder App.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(recipient, subject, html_content):
    """
    Send an email with the given content using external API
    """
    logger.info(f"Sending email to: {recipient}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Content length: {len(html_content)} characters")
    
    # For debugging purposes, also save the email content to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    email_debug_file = f"email_debug_{timestamp}.html"
    
    with open(email_debug_file, 'w') as f:
        f.write(html_content)
    
    logger.info(f"Email content saved to {email_debug_file} for debugging")
    
    # Use the external API to send the email
    try:
        # Get API hostname from environment variable with fallback to localhost
        if os.environ.get('ENV') == 'production':
            api_host = os.environ.get('API_HOST_PROD')
        else:
            api_host = os.environ.get('API_HOST')
        api_url = f"{api_host}/api/v1/send-custom-email"

        print(f"Sending email to {recipient} via API at {api_url}")
        
        # Prepare the payload for the API
        payload = {
            'email': recipient,
            'subject': subject,
            'html_content': html_content
        }
        
        # Send the request to the API
        response = requests.post(
            api_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info(f"Email successfully sent to {recipient} via API")
            return True
        else:
            logger.error(f"API returned error: {response.status_code}, {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send email via API: {str(e)}")
        return False

def send_birthday_notifications(notifications):
    """
    Send email notifications for upcoming birthdays
    """
    for notification in notifications:
        username = notification['username']
        email = notification['email']
        birthdays = notification['birthdays']
        
        # Skip if user has no email
        if not email:
            logger.warning(f"No email address for user {username}, skipping notification")
            continue
        
        # Format email content
        html_content = format_birthday_email(username, birthdays)
        
        # Set subject based on whether there are birthdays today
        today_birthdays = [b for b in birthdays if b['days_until'] == 0]
        if today_birthdays:
            subject = f"Birthday Reminder: {len(today_birthdays)} birthdays today!"
        else:
            subject = "Upcoming Birthday Reminders"
        
        # Send the email
        sent = send_email(email, subject, html_content)
        
        if sent:
            logger.info(f"Birthday notification email sent to {email}")
        else:
            logger.error(f"Failed to send birthday notification email to {email}")
            return False
    
    return True 