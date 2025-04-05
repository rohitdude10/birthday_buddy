#!/usr/bin/env python
"""
Setup Script for Scheduling Birthday Notifications

This script automatically sets up a cron job to run the birthday notification script
daily on Linux systems without requiring user input.
"""

import os
import sys
import platform
import subprocess
from datetime import datetime
from pathlib import Path
import tempfile
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("setup_notification")

def get_script_path():
    """Get the absolute path to the birthday_notifier.py script"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, 'birthday_notifier.py')
    return os.path.normpath(script_path)

def setup_linux_cron(run_time="08:00", force=True):
    """Set up a Linux cron job to run daily at the specified time
    
    Args:
        run_time (str): Time to run in HH:MM format (24-hour)
        force (bool): If True, override existing cron jobs without asking
    
    Returns:
        bool: True if successful, False otherwise
    """
    script_path = get_script_path()
    python_path = sys.executable
    script_dir = os.path.dirname(script_path)
    
    # Parse the run time
    try:
        hour, minute = map(int, run_time.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        logger.warning(f"Invalid time format: {run_time}. Using default (08:00).")
        hour, minute = 8, 0
    
    logger.info(f"Setting up Linux Cron Job to run at {hour:02d}:{minute:02d}")
    
    # Create the cron job entry
    cron_job = f"{minute} {hour} * * * cd {script_dir} && {python_path} {script_path} >> {script_dir}/cron.log 2>&1\n"
    
    # Get existing crontab
    try:
        process = subprocess.Popen(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        current_crontab, error = process.communicate()
        
        # If there's an error and it's not just "no crontab for user"
        if error and b"no crontab for" not in error:
            logger.error(f"Error getting current crontab: {error.decode().strip()}")
            return False
        
        current_crontab = current_crontab.decode()
    except Exception as e:
        logger.warning(f"Error accessing crontab: {str(e)}")
        current_crontab = ""
    
    # Check if the job already exists
    if script_path in current_crontab:
        logger.info("A cron job for birthday notifications already exists.")
        if not force:
            logger.info("Keeping existing cron job unchanged.")
            return True
        
        # Remove existing lines containing our script path
        logger.info("Removing existing cron job and adding a new one.")
        new_crontab_lines = []
        for line in current_crontab.splitlines():
            if script_path not in line:
                new_crontab_lines.append(line)
        current_crontab = '\n'.join(new_crontab_lines)
        if current_crontab and not current_crontab.endswith('\n'):
            current_crontab += '\n'
    
    # Add new cron job
    new_crontab = current_crontab + cron_job
    
    # Write to temp file and install
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write(new_crontab)
            temp_path = temp.name
        
        process = subprocess.Popen(['crontab', temp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        os.unlink(temp_path)  # Delete the temp file
        
        if error:
            logger.error(f"Error installing crontab: {error.decode().strip()}")
            return False
        
        logger.info(f"Cron job successfully installed to run daily at {hour:02d}:{minute:02d}")
        logger.info(f"Job will execute: {cron_job.strip()}")
        return True
    
    except Exception as e:
        logger.error(f"Error setting up cron job: {str(e)}")
        return False

def test_notification(silent=True):
    """Run the birthday notifier script once to test it
    
    Args:
        silent (bool): If True, suppresses output from the notification script
    """
    script_path = get_script_path()
    python_path = sys.executable
    
    logger.info("Testing Birthday Notification")
    logger.info(f"Running: {python_path} {script_path}")
    
    try:
        if silent:
            # Redirect output to null
            with open(os.devnull, 'w') as devnull:
                subprocess.run([python_path, script_path], stdout=devnull, stderr=devnull)
        else:
            subprocess.run([python_path, script_path])
        logger.info("Test completed successfully.")
    except Exception as e:
        logger.error(f"Error testing notification script: {str(e)}")

def main():
    """Main function to set up scheduled task based on OS"""
    logger.info("Birthday Notification Setup")
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version}")
    
    system = platform.system().lower()
    
    if system != 'linux':
        logger.error(f"This script only supports Linux systems.")
        logger.error(f"Detected OS: {platform.system()} {platform.release()}")
        sys.exit(1)
    
    # Make sure the notification script exists
    script_path = get_script_path()
    if not os.path.isfile(script_path):
        logger.error(f"Error: Birthday notification script not found at {script_path}")
        sys.exit(1)
    
    # Check if this is being run as part of deployment
    # Using environment variable to detect deployment
    if os.environ.get('DEPLOY_ENV') or '--auto' in sys.argv:
        # Automatically set up without prompting during deployment
        logger.info("Running in auto-deployment mode")
        run_time = "08:00"  # Default to 8 AM
        
        # Look for time setting in command line args
        for arg in sys.argv:
            if arg.startswith('--time='):
                run_time = arg.split('=')[1]
        
        # Set up cron job automatically
        if setup_linux_cron(run_time, force=True):
            # Run a silent test
            test_notification(silent=True)
            logger.info("Auto-deployment setup completed successfully.")
    else:
        # Interactive mode for manual setup
        logger.info("Running in interactive mode")
        
        # Get desired run time
        print("\nAt what time would you like the notification to run daily?")
        print("Format: HH:MM (24-hour format, e.g., 08:00 for 8 AM)")
        run_time = input("Time (default 08:00): ").strip() or "08:00"
        
        # Set up cron job
        if setup_linux_cron(run_time, force=False):
            # Offer to test the script
            test = input("\nWould you like to test the notification script now? (y/n): ")
            if test.lower() == 'y':
                test_notification(silent=False)
        
        print("\nSetup completed.")
        print("Make sure your email settings in the .env file are configured correctly.")

if __name__ == "__main__":
    main() 