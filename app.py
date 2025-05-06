import os
import uuid
import json
import subprocess
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
import cv_gen.generator as generator
from flask_login import login_required, current_user
from models import User, CVData, ContactMessage
from auth import auth as auth_blueprint
from extensions import db, login_manager
from forms import CVForm
from functools import wraps
import os
from flask import Flask
from dotenv import load_dotenv
from celery import Celery
from routes.route_path import RoutePath , routes as routes_blueprint
from extensions import db, init_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dashboard import dashboard
import logging





def create_app():

    # Load environment variables
    load_dotenv()
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Base configuration from .env with defaults
    app.config.from_mapping(
        # Flask Security
        SECRET_KEY=os.getenv('SECRET_KEY'),
        
        # Database Configuration
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        
        # File Uploads
        UPLOAD_FOLDER=os.path.join('instance', 'uploads'),
        LATEX_OUTPUT_FOLDER=os.path.join('instance', 'latex_outputs'),
        PDF_OUTPUT_FOLDER=os.path.join('instance', 'pdf_outputs'),
        ALLOWED_EXTENSIONS={'json', 'txt'},
        MAX_CONTENT_LENGTH= eval(os.getenv('MAX_CONTENT_LENGTH')),
        
        # Email Configuration
        MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
        MAIL_PORT=os.getenv('MAIL_PORT', 587),
        MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', True),
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        
        # Rate Limiting
        RATE_LIMIT=os.getenv('RATE_LIMIT', "200 per day, 50 per hour")
    )

    # Initialize extensions
    init_app(app) 

    # Configure Celery if available
    celery = None
    if os.getenv('CELERY_BROKER_URL'):
        try:
            celery = Celery(__name__, broker=os.getenv('CELERY_BROKER_URL'))
            celery.conf.update(app.config)
        except ImportError:
            app.logger.warning("Celery not installed. Celery integration disabled.")
            pass
    
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


    from logging.handlers import RotatingFileHandler
    import logging

    def setup_logging():
        try:
            # Get absolute path to log file
            log_file = os.path.join('opt/', 'app.log')

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
    setup_logging()


    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LATEX_OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(routes_blueprint)  
    app.register_blueprint(dashboard)      

    
    # Helper functions
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def cleanup_old_files(directory, days=1):
        now = datetime.now()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if now - modified_time > timedelta(days=days):
                    os.remove(filepath)
                    app.logger.info(f"Removed old file: {filepath}")

    def json_response(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, tuple):
                response, status = result
            else:
                response, status = result, 200
            return jsonify(response), status
        return wrapper

    # Routes
    @app.route('/')
    def index():
        return render_template( RoutePath.home_index )

    @app.route('/health')
    @json_response
    def health_check():
        try:
            db.session.execute('SELECT 1')
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500

    # @app.route('/dashboard')
    # @login_required
    # def dashboard():
    #     if not current_user.is_authenticated:
    #         return redirect( url_for('auth.signin') )
        
    #     cv_data = CVData.query.filter_by(user_id=current_user.id).first()
    #     form = CVForm()
    #     return render_template( RoutePath.dashboard_index, 
    #                         cv_data=cv_data.data if cv_data else None,
    #                         form=form)

    @app.route('/upload', methods=['POST'])
    def upload_file():
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash("No file part")
            app.logger.warning("No file part in request")
            return render_template( RoutePath.home_index )
        
        file = request.files['file']
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash("No selected file")
            app.logger.warning("Empty filename in file upload")
            return render_template( RoutePath.home_index )
        
        if file and allowed_file(file.filename):
            unique_id = uuid.uuid4()
            safe_filename = secure_filename(file.filename)
            filename = f"{unique_id}_{safe_filename}"
            
            # Debugging: Log all form data
            app.logger.debug(f"Form data received: {request.form.to_dict()}")
            
            # Get selected template (default to professional if not specified)
            try:
                template_style = request.form.get('template', 'professional')
                app.logger.info(f"Selected template style: {template_style}")
                
                # Verify upload directories exist
                for folder in ['UPLOAD_FOLDER', 'LATEX_OUTPUT_FOLDER', 'PDF_OUTPUT_FOLDER']:
                    if not os.path.exists(app.config[folder]):
                        os.makedirs(app.config[folder])
                        app.logger.info(f"Created directory: {app.config[folder]}")
                
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                latex_output_path = os.path.join(app.config['LATEX_OUTPUT_FOLDER'], f"{unique_id}.tex")
                pdf_filename = f"{unique_id}.pdf"
                pdf_output_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
                
                app.logger.info(f"File paths configured - "
                            f"Input: {input_path}, "
                            f"LaTeX Output: {latex_output_path}, "
                            f"PDF Output: {pdf_output_path}")
                
                # Verify file content before saving
                #if file.content_length == 0:
                #   app.logger.error("Uploaded file is empty")
                #    flash("Uploaded file is empty")
                #    return render_template( RoutePath.home_index )
                
                file.save(input_path)
                app.logger.info(f"Successfully saved uploaded file to {input_path}")
                
                # Verify file was actually saved
                if not os.path.exists(input_path):
                    app.logger.error(f"File save verification failed - {input_path} doesn't exist")
                    flash("Failed to save uploaded file")
                    return render_template( RoutePath.home_index )
                else:
                    app.logger.info(f"File save verified - size: {os.path.getsize(input_path)} bytes")
                
            except IOError as e:
                app.logger.error(f"File operation failed: {str(e)}", exc_info=True)
                flash("File system error occurred")
                return render_template( RoutePath.home_index )
            except Exception as e:
                app.logger.error(f"Unexpected error during file setup: {str(e)}", exc_info=True)
                flash("Unexpected error occurred")
                return render_template( RoutePath.home_index )
            
            try:
                # Generate LaTeX from input with selected template
                app.logger.info("Starting LaTeX generation")
                cv_generator = generator.Generator(input_path)#, template=template_style)
                cv_str = cv_generator.make_cv()
                app.logger.info(f"Generated LaTeX content (length: {len(cv_str)} characters)")
                
                try:
                    with open(latex_output_path, "w") as tex_file:
                        app.logger.info(f"Attempting to write LaTeX output to: {latex_output_path}")
                        tex_file.write(cv_str)
                        app.logger.info(f"Successfully wrote {len(cv_str)} characters to {latex_output_path}")
                    
                    # Verify LaTeX file was written
                    if not os.path.exists(latex_output_path):
                        app.logger.error(f"LaTeX file write verification failed - {latex_output_path} doesn't exist")
                        flash("Failed to generate LaTeX output")
                        return render_template( RoutePath.home_index )
                    else:
                        app.logger.info(f"LaTeX file verified - size: {os.path.getsize(latex_output_path)} bytes")
                        
                except IOError as e:
                    app.logger.error(f"Failed to write to {latex_output_path}: {str(e)}", exc_info=True)
                    flash("Failed to generate LaTeX output")
                    return render_template( RoutePath.home_index )
                except Exception as e:
                    app.logger.error(f"Unexpected error while writing to {latex_output_path}: {str(e)}", exc_info=True)
                    flash("Unexpected error during LaTeX generation")
                    return render_template( RoutePath.home_index )
                
                # Convert LaTeX to PDF
                app.logger.info("Starting PDF generation with pdflatex")
                try:
                    result = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "-output-directory", app.config['PDF_OUTPUT_FOLDER'], latex_output_path],
                        capture_output=True,
                        text=True,
                        timeout=30  # Add timeout to prevent hanging
                    )
                    
                    app.logger.debug(f"pdflatex stdout: {result.stdout}")
                    app.logger.debug(f"pdflatex stderr: {result.stderr}")
                    
                    
                    # Verify PDF was created
                    if not os.path.exists(pdf_output_path):
                        app.logger.error(f"PDF output verification failed - {pdf_output_path} doesn't exist")
                        flash("PDF generation failed")
                        return render_template( RoutePath.home_index )
                    else:
                        app.logger.info(f"PDF generated successfully - size: {os.path.getsize(pdf_output_path)} bytes")
                    
                    # Clean up auxiliary files
                    base_filename = os.path.splitext(os.path.basename(latex_output_path))[0]
                    extensions_to_delete = ['aux', 'log', 'out']
                    for ext in extensions_to_delete:
                        aux_file = os.path.join(app.config['PDF_OUTPUT_FOLDER'], f"{base_filename}.{ext}")
                        if os.path.exists(aux_file):
                            try:
                                os.remove(aux_file)
                                app.logger.debug(f"Removed auxiliary file: {aux_file}")
                            except Exception as e:
                                app.logger.warning(f"Could not remove {aux_file}: {str(e)}")
                    
                except subprocess.TimeoutExpired:
                    app.logger.error("pdflatex timed out")
                    flash("PDF generation timed out")
                    return render_template( RoutePath.home_index )
                except Exception as e:
                    app.logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
                    flash("PDF generation failed")
                    return render_template( RoutePath.home_index )
                
                # Check if request wants JSON response (for AJAX)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    app.logger.info("Returning JSON response for AJAX request")
                    return jsonify({
                        'success': True,
                        'download_link': url_for('download_file', filename=pdf_filename),
                        'preview_link': url_for('preview_pdf', filename=pdf_filename)
                    })
                
                # Regular form response
                app.logger.info("File processing completed successfully")
                flash("File uploaded and converted successfully!")
                return render_template( RoutePath.home_index ,
                                    download_link=pdf_filename,
                                    preview_link=url_for('preview_pdf', filename=pdf_filename))
                
            except Exception as e:
                app.logger.error(f"Processing error: {str(e)}", exc_info=True)
                flash(f"An error occurred: {str(e)}")
                return render_template( RoutePath.home_index )
        else:
            app.logger.warning(f"Invalid file type attempted: {file.filename}")
            flash("Only .txt and .json files are allowed.")
            return render_template( RoutePath.home_index )

    def generate_pdf(input_path, unique_id):
        """Helper function to generate PDF from input file"""
        latex_output_path = os.path.join(app.config['LATEX_OUTPUT_FOLDER'], f"{unique_id}.tex")
        pdf_filename = f"{unique_id}.pdf"
        pdf_output_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)

        cv_generator = generator.Generator(input_path)
        cv_str = cv_generator.make_cv()

        with open(latex_output_path, "w") as tex_file:
            tex_file.write(cv_str)

        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", 
            app.config['PDF_OUTPUT_FOLDER'], latex_output_path],
            capture_output=True,
            text=True
        )

        # Clean up auxiliary files
        base_filename = os.path.splitext(os.path.basename(latex_output_path))[0]
        for ext in ['aux', 'log', 'out']:
            aux_file = os.path.join(app.config['PDF_OUTPUT_FOLDER'], f"{base_filename}.{ext}")
            if os.path.exists(aux_file):
                os.remove(aux_file)

        return pdf_filename

    @app.route('/download/<filename>')
    def download_file(filename):
        return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], filename, as_attachment=True)

    @app.route('/preview/<filename>')
    def preview_pdf(filename):
        return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], filename)

    @app.route('/sample-json')
    def sample_json():
        """Return a sample JSON structure for CV creation"""
        sample = {
            "personal_info": {
                "name": "John Doe",
                "location": "New York, NY",
                "email": "john.doe@example.com",
                "phone": "+1 (123) 456-7890",
                "linkedin": "https://linkedin.com/in/johndoe",
                "github": "https://github.com/johndoe"
            },
            "content": {
                "objective": "Experienced software engineer seeking challenging opportunities in AI development.",
                "education": [
                    {
                        "university": "Massachusetts Institute of Technology",
                        "degree": "B.S. Computer Science",
                        "startDate": "2016-09-01",
                        "endDate": "2020-05-31",
                        "gpa": "3.8/4.0",
                        "coursework": "Data Structures, Algorithms, Machine Learning, Computer Vision"
                    }
                ],
                "experience": [
                    {
                        "company": "Google",
                        "role": "Software Engineer",
                        "startDate": "2020-06-01",
                        "endDate": "Present",
                        "responsibilities": [
                            "Developed and maintained backend services using Go and Python",
                            "Collaborated with cross-functional teams to implement new features",
                            "Optimized database queries improving performance by 30%"
                        ]
                    }
                ],
                "projects": [
                    {
                        "title": "AI Image Recognition",
                        "github_link": "https://github.com/johndoe/ai-image",
                        "responsibilities": [
                            "Implemented CNN architecture achieving 95% accuracy",
                            "Created data pipeline processing 1TB of images daily",
                            "Deployed model to production environment using Docker and Kubernetes"
                        ]
                    }
                ],
                "languages": ["Python", "JavaScript", "Go", "C++"],
                "technologies": ["React", "TensorFlow", "Docker", "AWS", "PostgreSQL"]
            }
        }
        
        return jsonify(sample)

    @app.route('/contact', methods=['POST'])
    @limiter.limit("5 per minute") 
    @json_response
    def contact():
        """Handle contact form submissions"""
        data = request.get_json()
        if not all(key in data for key in ['name', 'email', 'message']):
            return {'success': False, 'message': 'Missing required fields'}, 400
        
        try:
            message = ContactMessage(
                name=data['name'],
                email=data['email'],
                message=data['message']
            )
            db.session.add(message)
            db.session.commit()
            return {'success': True, 'message': 'Message received!'}, 200
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}, 500

  
    @app.errorhandler(404)
    def page_not_found(e):

        # Log the error and get the source of the request
        app.logger.warning(f"Page not found: {request.url} , {request.method}" )

        return render_template( RoutePath.errors_404_index ), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template( RoutePath.errors_500_index ), 500
    
    @app.context_processor
    def inject_route_path():
        return {'RoutePath': RoutePath}

    # Scheduled cleanup
    @app.before_request
    def scheduled_cleanup():
        if request.endpoint != 'static':
            for folder in [app.config['UPLOAD_FOLDER'], app.config['LATEX_OUTPUT_FOLDER']]:
                cleanup_old_files(folder, days=1)

    return app
