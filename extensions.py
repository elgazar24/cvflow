from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail  # For password reset emails
from itsdangerous import URLSafeTimedSerializer  # For generating secure tokens

# Database
db = SQLAlchemy()

# Authentication
login_manager = LoginManager()

# Email
mail = Mail()

# Token generation
def make_serializer(app):
    return URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Initialize all extensions
def init_app(app):
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' 
    mail.init_app(app)
    # No initialization needed for the serializer