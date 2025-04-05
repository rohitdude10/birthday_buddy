# Birthday Buddy - Birthday Reminder Application

A modern Flask web application to keep track of birthdays with user authentication and a clean, responsive UI.

## Features

- User authentication with JWT tokens
- Modern and responsive UI using Bootstrap 5
- CSRF protection for secure forms
- Upcoming birthdays dashboard
- Grid and list view for birthday management
- MySQL database for storage and management
- Mobile-friendly design

## Local Development Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd birthday-buddy
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```
   
   Update the .env file to include your database credentials:
   ```
   DATABASE_URI=mysql+pymysql://USERNAME:${PASSWORD}@hostname:port/database
   PASSWORD=your_database_password
   USERNAME=your_database_username
   DB_NAME=your_database_name
   ```
   
6. Test the database connection:
   ```bash
   python test_mysql_connection.py
   ```

7. Run the application:
   ```bash
   python app.py
   ```

8. Open your browser and go to http://localhost:5000

## Production Deployment

### Environment Preparation

1. Set your environment to production:
   ```
   ENV=production
   ```

2. Generate and set secure random keys for `SECRET_KEY` and `JWT_SECRET_KEY`

3. Configure your database connection in the .env file:
   ```
   DATABASE_URI=mysql+pymysql://USERNAME:${PASSWORD}@hostname:port/database
   PASSWORD=your_database_password
   USERNAME=your_database_username
   DB_NAME=your_database_name
   ```

### Deploy to a VPS (e.g., Ubuntu server)

1. Install required system packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools postgresql postgresql-contrib nginx
   ```

2. Clone the repository and set up a virtual environment as in the development setup.

3. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

4. Create a systemd service file `/etc/systemd/system/birthday-buddy.service`:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Birthday Buddy application
   After=network.target

   [Service]
   User=<your-user>
   Group=www-data
   WorkingDirectory=/path/to/birthday-buddy
   Environment="PATH=/path/to/birthday-buddy/venv/bin"
   EnvironmentFile=/path/to/birthday-buddy/.env
   ExecStart=/path/to/birthday-buddy/venv/bin/gunicorn --workers 3 --bind unix:birthday-buddy.sock -m 007 wsgi:app

   [Install]
   WantedBy=multi-user.target
   ```

5. Enable and start the service:
   ```bash
   sudo systemctl start birthday-buddy
   sudo systemctl enable birthday-buddy
   ```

6. Configure Nginx as a reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/path/to/birthday-buddy/birthday-buddy.sock;
       }
   }
   ```

7. Enable the Nginx site and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/birthday-buddy /etc/nginx/sites-enabled
   sudo systemctl restart nginx
   ```

8. Set up SSL with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your_domain.com
   ```

### Deploy to Heroku

1. Install the Heroku CLI and log in:
   ```bash
   heroku login
   ```

2. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

3. Set environment variables:
   ```bash
   heroku config:set ENV=production
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set JWT_SECRET_KEY=your-jwt-secret-key
   ```

4. Add a PostgreSQL database:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. Deploy:
   ```bash
   git push heroku main
   ```

6. Run database migrations if needed:
   ```bash
   heroku run python
   ```
   
   Then in the Python shell:
   ```python
   from app import app, db
   with app.app_context():
       db.create_all()
   ```

## Security Considerations

The application implements several security best practices:
- CSRF protection for all forms
- Secure password hashing with passlib
- JWT for secure authentication
- HTTP security headers
- Content Security Policy
- Environment-based configuration

## License

[MIT License](LICENSE)

## Setup Instructions

1. Clone this repository or download the files
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Database Setup:
   - The application uses a MySQL database
   - To reset the database: `python reset_db.py`
   - To test the connection: `python test_mysql_connection.py`
5. Run the application:
   ```bash
   python app.py
   ```
6. Open your web browser and navigate to `