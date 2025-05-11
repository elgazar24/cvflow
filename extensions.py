from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail  # For password reset emails
from itsdangerous import URLSafeTimedSerializer  # For generating secure tokens
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import logging
from celery import Celery
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Database
db = SQLAlchemy()

# Authentication
login_manager = LoginManager()

# Email
mail = Mail()

# Token generation
def make_serializer(app):
    return URLSafeTimedSerializer(app.config['SECRET_KEY'])


def setup_logging(app):
    try:
        # Get absolute path to log file
        log_file = '../logs/app.log'
        print(log_file)
        # Clear any existing handlers
        app.logger.handlers.clear()
        # Create rotating file handler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=1024*1024,  # 1MB
            backupCount=3,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        handler.setLevel(logging.INFO)
        # Add handler to Flask's logger
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        # Test logging
        app.logger.info("Logging setup completed successfully")
        app.logger.info(f"Log file location: {log_file}")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize logging: {str(e)}")
        # Fallback to stderr
        logging.basicConfig(level=logging.INFO)

    # Initialize logging when app starts

def get_celery(app):
    celery = None  # Initialize with None by default
    
    if app.config.get('CELERY_BROKER_URL'):
        try:
            celery = Celery(
                app.import_name,
                broker=app.config['CELERY_BROKER_URL'],
                backend=app.config.get('CELERY_RESULT_BACKEND')
            )
            celery.conf.update(app.config)
            # Set timezone if needed
            celery.conf.timezone = app.config.get('CELERY_TIMEZONE', 'UTC')
        except ImportError:
            app.logger.warning("Celery not installed. Celery integration disabled.")
    
    return celery

def get_limiter(app):
    # Initialize Flask-Limiter if available
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri="memory://",
            strategy="fixed-window" 
            )
        limiter.init_app(app)
    except ImportError:
        app.logger.warning("Flask-Limiter not installed. Rate limiting disabled.")
        limiter = None

    return limiter


def check_required_directories(app):
    """Ensure all required directories exist with proper permissions."""
    required_directories = {
        'UPLOAD_FOLDER': 0o775,
        'LATEX_OUTPUT_FOLDER': 0o775,
        'PDF_OUTPUT_FOLDER': 0o775,
        'IMAGE_UPLOAD_FOLDER': 0o775,
        'MOCK_FOLDER': 0o775
    }
    
    # First ensure instance path exists
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path, mode=0o775)
    
    for config_key, permissions in required_directories.items():
        try:
            directory = app.config.get(config_key)
            if not directory:
                raise ValueError(f"Configuration '{config_key}' is not set")
                
            if not os.path.exists(directory):
                os.makedirs(directory, mode=permissions)
                print(f"Created directory: {directory}")
            os.chmod(directory, permissions)
        except Exception as e:
            app.logger.error(f"Failed to setup directory {config_key}: {str(e)}")
            raise

# Initialize all extensions
def init_app(app):

    setup_logging(app)

    # Load environment variables
    load_dotenv()

    # Base configuration from .env with defaults
    app.config.from_mapping(

        # Site Data
        SITE_URL=os.getenv('SITE_URL', 'cvflow.live'),
        SITE_TITLE=os.getenv('SITE_TITLE', 'CVFlow'),
        SITE_DESCRIPTION=os.getenv('SITE_DESCRIPTION', 'A CV generator website'),

        # General Configuration
        DEBUG=os.getenv('DEBUG', False),


        # Flask Security
        SECRET_KEY=os.getenv('SECRET_KEY'),
        
        # Database Configuration
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        
        # File Uploads
        UPLOAD_FOLDER=os.path.join('instance', 'uploads'),
        LATEX_OUTPUT_FOLDER=os.path.join('instance', 'latex_outputs'),
        PDF_OUTPUT_FOLDER=os.path.join('instance', 'pdf_outputs'),
        IMAGE_UPLOAD_FOLDER=os.path.join('instance', 'image_uploads'),
        MOCK_FOLDER = os.path.join('mock'),
        ALLOWED_EXTENSIONS={'json', 'txt','docx','doc'},
        MAX_CONTENT_LENGTH= eval(os.getenv('MAX_CONTENT_LENGTH')),

        
        # Email Configuration
        MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
        MAIL_PORT=os.getenv('MAIL_PORT', 587),
        MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', True),
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        
        # Rate Limiting
        RATE_LIMIT=os.getenv('RATE_LIMIT', "200 per day, 50 per hour"),

        # Celery Configuration
        CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL'),
        CELERY_RESULT_BACKEND=os.getenv('CELERY_RESULT_BACKEND'),

        AI_API_KEY=os.getenv('AI_API_KEY'),
        NETMIND_API_KEY=os.getenv('NETMIND_API_KEY')
    )

    # Initialize Flask-SQLAlchemy and Flask-Migrate
    migrate = Migrate(app, db)
    db.init_app(app)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' 

    # Initialize Flask-Mail
    mail.init_app(app)


    # Check required directories
    check_required_directories(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created!")
