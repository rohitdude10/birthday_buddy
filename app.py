from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dateutil import parser
import calendar
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
from sqlalchemy import or_
from flask_wtf.csrf import CSRFProtect, CSRFError
import os
from dotenv import load_dotenv
import logging
import pymysql

# Set up PyMySQL to work with SQLAlchemy
pymysql.install_as_MySQLdb()

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
# Use environment variables for sensitive settings with fallbacks
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# MySQL Database Configuration
# Construct the SQLAlchemy URI directly with the actual values
db_uri = os.environ.get('DATABASE_SERVICE_URI')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'connect_args': {
        'connect_timeout': 10,
        'read_timeout': 10,
        'write_timeout': 10
    }
}

# CSRF Configuration
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['WTF_CSRF_ENABLED'] = True

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = os.environ.get('ENV', 'development') == 'production'  # Only True in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable JWT's CSRF protection to avoid conflicts
jwt = JWTManager(app)

# Enable CSRF protection globally but with our configuration
csrf = CSRFProtect(app)

# Security headers
@app.after_request
def add_security_headers(response):
    # Prevent content-type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; img-src 'self' https://images.unsplash.com data:;"
    return response

db = SQLAlchemy(app)

# Custom error handler for CSRF errors
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('The form submission expired. Please try again.', 'danger')
    return redirect(request.full_path)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    birthdays = db.relationship('Birthday', backref='user', lazy=True)
    notifications = db.relationship('BirthdayNotification', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)
        
    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

class Birthday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Changed to nullable=True temporarily
    notifications = db.relationship('BirthdayNotification', backref='birthday', lazy=True)

    def __repr__(self):
        return f'<Birthday {self.name}>'

class BirthdayNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    birthday_id = db.Column(db.Integer, db.ForeignKey('birthday.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    year_notified = db.Column(db.Integer, nullable=False) # The year of the birthday we notified about
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BirthdayNotification for {self.birthday_id} sent on {self.notification_date}>'

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/api/upcoming_birthdays')
@jwt_required()
def upcoming_birthdays():
    # Get current user
    current_user_id = int(get_jwt_identity())
    
    # Get query parameters
    days = request.args.get('days', default=30, type=int)
    
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    # Find birthdays in the upcoming days for the current user and any without a user_id
    birthdays = []
    
    # Get birthdays belonging to this user and any without a user_id
    birthday_records = Birthday.query.filter(
        or_(
            Birthday.user_id == current_user_id,
            Birthday.user_id == None
        )
    ).all()
    
    for birthday in birthday_records:
        # Get this year's birthday
        this_year_bday = birthday.date.replace(year=today.year)
        
        # If birthday already happened this year, look at next year
        if this_year_bday < today:
            this_year_bday = this_year_bday.replace(year=today.year + 1)
        
        # Check if birthday is within the requested range
        if today <= this_year_bday <= end_date:
            days_until = (this_year_bday - today).days
            age = this_year_bday.year - birthday.date.year
            
            birthdays.append({
                'id': birthday.id,
                'name': birthday.name,
                'date': birthday.date.strftime('%Y-%m-%d'),
                'this_year_date': this_year_bday.strftime('%Y-%m-%d'),
                'days_until': days_until,
                'age': age,
                'notes': birthday.notes
            })
    
    # Sort by days until birthday
    birthdays.sort(key=lambda x: x['days_until'])
    
    return jsonify({
        'upcoming_birthdays': birthdays,
        'total': len(birthdays),
        'days_checked': days
    })

@app.route('/')
def index():
    # Instead of manually checking for the cookie and using try/except,
    # we can use verify_jwt_in_request with optional=True
    # This will not raise an exception if the token is missing or invalid
    verify_jwt_in_request(optional=True)
    
    # Get the identity (will be None if no valid token)
    jwt_identity = get_jwt_identity()
    
    if jwt_identity:
        # User is authenticated, convert string ID to integer
        current_user_id = int(jwt_identity)
        
        # Get user's birthdays and any without a user_id (for transition period)
        # Using SQLAlchemy OR condition
        birthdays = Birthday.query.filter(
            or_(
                Birthday.user_id == current_user_id,
                Birthday.user_id == None  # Birthdays without a user_id
            )
        ).order_by(Birthday.date).all()
        
        # Calculate upcoming birthdays (next 30 days)
        today = datetime.now().date()
        end_date = today + timedelta(days=30)
        
        upcoming = []
        
        for birthday in birthdays:
            # Get this year's birthday
            this_year_bday = birthday.date.replace(year=today.year)
            
            # If birthday already happened this year, look at next year
            if this_year_bday < today:
                this_year_bday = this_year_bday.replace(year=today.year + 1)
            
            # Check if birthday is within the next 30 days
            if today <= this_year_bday <= end_date:
                days_until = (this_year_bday - today).days
                age = this_year_bday.year - birthday.date.year
                
                upcoming.append({
                    'id': birthday.id,
                    'name': birthday.name,
                    'date': birthday.date,
                    'this_year_date': this_year_bday,
                    'days_until': days_until,
                    'age': age,
                    'notes': birthday.notes
                })
        
        # Sort by days until birthday
        upcoming.sort(key=lambda x: x['days_until'])
        
        return render_template('index.html', birthdays=birthdays, upcoming=upcoming)
    else:
        # User not logged in, show welcome page
        return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        # Validate form data
        error = None
        if not username or not email or not password:
            error = 'All fields are required.'
        elif password != password_confirm:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists.'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'
            
        if error:
            flash(error, 'danger')
            return render_template('signup.html')
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Create the JWT token with the user ID as a string
            access_token = create_access_token(identity=str(user.id))
            
            # Set the JWT cookies in the response
            response = make_response(redirect(url_for('index')))
            set_access_cookies(response, access_token)
            
            flash('Login successful!', 'success')
            return response
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    unset_jwt_cookies(response)
    flash('You have been logged out.', 'info')
    return response

@app.route('/add', methods=['GET', 'POST'])
@jwt_required()
def add_birthday():
    # For GET requests, just render the template
    if request.method == 'GET':
        return render_template('add.html')
    
    # For POST requests, process the form
    if request.method == 'POST':
        try:
            name = request.form['name']
            date_str = request.form['date']
            notes = request.form['notes']
            current_user_id = int(get_jwt_identity())
            
            date = parser.parse(date_str).date()
            birthday = Birthday(name=name, date=date, notes=notes, user_id=current_user_id)
            db.session.add(birthday)
            db.session.commit()
            flash('Birthday added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding birthday: {str(e)}', 'danger')
            return render_template('add.html')

@app.route('/delete/<int:id>')
@jwt_required()
def delete_birthday(id):
    current_user_id = int(get_jwt_identity())
    birthday = Birthday.query.get_or_404(id)
    
    # Check if the birthday belongs to the current user or has no user_id
    if birthday.user_id is not None and birthday.user_id != current_user_id:
        flash('Not authorized to delete this birthday.', 'danger')
        return redirect(url_for('index'))
    
    # If birthday has no user_id, assign it to the current user before deleting
    # This prevents other users from deleting it
    if birthday.user_id is None:
        birthday.user_id = current_user_id
        db.session.commit()
    
    db.session.delete(birthday)
    db.session.commit()
    flash('Birthday deleted successfully!', 'success')
    return redirect(url_for('index'))

# Add this function to fetch upcoming birthdays in the next 2 days
def get_upcoming_birthdays_next_two_days():
    """
    Fetch all upcoming birthdays in the next 2 days for all users
    Returns a dictionary with user_id as key and a list of their upcoming birthdays as value
    """
    today = datetime.now().date()
    end_date = today + timedelta(days=2)
    
    # Dictionary to store user_id -> [upcoming birthdays]
    user_birthdays = {}
    
    # Get all users
    users = User.query.all()
    
    for user in users:
        # Get birthdays for this user
        birthdays = Birthday.query.filter_by(user_id=user.id).all()
        upcoming = []
        
        for birthday in birthdays:
            # Get this year's birthday
            this_year_bday = birthday.date.replace(year=today.year)
            
            # If birthday already happened this year, look at next year
            if this_year_bday < today:
                this_year_bday = this_year_bday.replace(year=today.year + 1)
            
            # Check if birthday is within the next 2 days
            if today <= this_year_bday <= end_date:
                days_until = (this_year_bday - today).days
                age = this_year_bday.year - birthday.date.year
                
                upcoming.append({
                    'id': birthday.id,
                    'name': birthday.name,
                    'date': birthday.date,
                    'this_year_date': this_year_bday,
                    'days_until': days_until,
                    'age': age,
                    'notes': birthday.notes
                })
        
        # If this user has upcoming birthdays, add to dictionary
        if upcoming:
            # Sort by days until birthday
            upcoming.sort(key=lambda x: x['days_until'])
            user_birthdays[user.id] = {
                'user': user,
                'birthdays': upcoming
            }
    
    return user_birthdays

# Add a route to manually test the upcoming birthdays feature
@app.route('/api/upcoming_birthdays_two_days')
@jwt_required()
def upcoming_birthdays_two_days():
    # Get current user
    current_user_id = int(get_jwt_identity())
    
    # Get all upcoming birthdays for all users
    all_upcoming = get_upcoming_birthdays_next_two_days()
    
    # Extract just the current user's birthdays, if any
    upcoming_birthdays = []
    if current_user_id in all_upcoming:
        upcoming_birthdays = all_upcoming[current_user_id]['birthdays']
    
    return jsonify({
        'upcoming_birthdays': upcoming_birthdays,
        'total': len(upcoming_birthdays),
        'days_checked': 2
    })

# Add a route to view notification history
@app.route('/notification_history')
@jwt_required()
def notification_history():
    # Get current user
    current_user_id = int(get_jwt_identity())
    
    # Get all notifications for this user
    notifications = BirthdayNotification.query.filter_by(user_id=current_user_id).order_by(
        BirthdayNotification.notification_date.desc()
    ).all()
    
    # Format for display
    notification_data = []
    
    for notification in notifications:
        birthday = Birthday.query.get(notification.birthday_id)
        if birthday:
            notification_data.append({
                'id': notification.id,
                'birthday_name': birthday.name,
                'notification_date': notification.notification_date.strftime('%Y-%m-%d'),
                'year_notified': notification.year_notified,
                'birthday_date': birthday.date.strftime('%Y-%m-%d'),
            })
    
    return jsonify({
        'notification_history': notification_data,
        'total': len(notification_data)
    })

if __name__ == '__main__':
    # In production, don't run with debug=True
    if os.environ.get('ENV') == 'production':
        # Production settings 
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
    else:
        # Development settings
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)