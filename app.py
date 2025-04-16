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
    from extensions import db, login_manager, mail, init_app
    init_app(app)


    # Configure Celery if available
    celery = None
    if os.getenv('CELERY_BROKER_URL'):
        try:
            from celery import Celery
            celery = Celery(__name__, broker=os.getenv('CELERY_BROKER_URL'))
            celery.conf.update(app.config)
        except ImportError:
            app.logger.warning("Celery not installed. Celery integration disabled.")
            pass
    
    # Initialize Flask-Limiter if available
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(key_func=get_remote_address)
        limiter.init_app(app)
    except ImportError:
        app.logger.warning("Flask-Limiter not installed. Rate limiting disabled.")
        limiter = None

    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LATEX_OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_blueprint)

    # Create database tables
    with app.app_context():
        db.create_all()
    
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
        return render_template('index.html')

    @app.route('/health')
    @json_response
    def health_check():
        try:
            db.session.execute('SELECT 1')
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500

    @app.route('/dashboard')
    @login_required
    def dashboard():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.signin'))
        
        cv_data = CVData.query.filter_by(user_id=current_user.id).first()
        form = CVForm()
        return render_template('dashboard.html', 
                            cv_data=cv_data.data if cv_data else None,
                            form=form)

    @app.route('/upload', methods=['POST'])
    def upload_file():
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash("No file part")
            return render_template('index.html')
        
        file = request.files['file']
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash("No selected file")
            return render_template('index.html')
        
        if file and allowed_file(file.filename):
            unique_id = uuid.uuid4()
            safe_filename = secure_filename(file.filename)
            filename = f"{unique_id}_{safe_filename}"
            
            # Get selected template (default to professional if not specified)
            template_style = request.form.get('template', 'professional')
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            latex_output_path = os.path.join(app.config['LATEX_OUTPUT_FOLDER'], f"{unique_id}.tex")
            pdf_filename = f"{unique_id}.pdf"
            pdf_output_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
            file.save(input_path)
            try:
                # Generate LaTeX from input with selected template
                cv_generator = generator.Generator(input_path)#, template=template_style)
                cv_str = cv_generator.make_cv()
                with open(latex_output_path, "w") as tex_file:
                    tex_file.write(cv_str)
                # Convert LaTeX to PDF
                # Run pdflatex
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", app.config['PDF_OUTPUT_FOLDER'], latex_output_path],
                    capture_output=True,
                    text=True
                )
                # Remove auxiliary files (keep only the PDF)
                base_filename = os.path.splitext(os.path.basename(latex_output_path))[0]
                extensions_to_delete = ['aux', 'log', 'out']  # add more if needed
                for ext in extensions_to_delete:
                    aux_file = os.path.join(app.config['PDF_OUTPUT_FOLDER'], f"{base_filename}.{ext}")
                    if os.path.exists(aux_file):
                        os.remove(aux_file)
                
                # Handle potential LaTeX errors
                # if result.returncode != 0:
                #     flash("Error generating PDF. Please check your JSON format.")
                #     app.logger.error(f"LaTeX Error: {result.stderr}")
                #     return render_template('index.html')
                
                # Check if request wants JSON response (for AJAX)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'download_link': url_for('download_file', filename=pdf_filename),
                        'preview_link': url_for('preview_pdf', filename=pdf_filename)
                    })
                
                # Regular form response
                flash("File uploaded and converted successfully!")
                return render_template('index.html',
                                    download_link=pdf_filename,
                                    preview_link=url_for('preview_pdf', filename=pdf_filename))
            except Exception as e:
                flash(f"An error occurred: {str(e)}")
                app.logger.error(f"Error: {str(e)}")
                return render_template('index.html')
        else:
            flash("Only .txt and .json files are allowed.")

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

    @app.route('/save_cv', methods=['POST'])
    @login_required
    def save_cv():
        try:
            # Get raw JSON data
            raw_data = request.get_json()
            
            # Debug print to see what's actually received
            app.logger.debug(f"Received data: {raw_data}")
            
            # Validate we got data
            if not raw_data:
                return jsonify({'success': False, 'error': 'No data received'}), 400

            # Get or create CV data
            cv_data = CVData.query.filter_by(user_id=current_user.id).first()

            if cv_data:
                # Update existing data
                cv_data.data = raw_data
            else:
                # Create new entry
                cv_data = CVData(user_id=current_user.id, data=raw_data)
                db.session.add(cv_data)
            
            db.session.commit()
            return jsonify({'success': True}), 200
            
        except Exception as e:
            app.logger.error(f"Error saving CV: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False, 
                'error': str(e),
                'received_data': raw_data  # For debugging
            }), 500

    @app.route('/preview_pdf_dashboard')
    @login_required
    def preview_pdf_dashboard():
        cv_data = CVData.query.filter_by(user_id=current_user.id).first()

        print("cv_data", cv_data)
        if not cv_data:
            flash("No CV data found")
            send_from_directory(app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")
        
        try:
            unique_id = uuid.uuid4()
            pdf_filename = generate_pdf_from_data(cv_data.data, unique_id)
            return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
        except Exception as e:
            # flash(f"Error generating PDF: {str(e)}")
            return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")

    @app.route('/download_pdf_dashboard')
    @login_required
    def download_pdf_dashboard():
        cv_data = CVData.query.filter_by(user_id=current_user.id).first()
        if not cv_data:
            flash("No CV data found")
            return redirect(url_for('dashboard'))
        
        try:
            unique_id = uuid.uuid4()
            pdf_filename = generate_pdf_from_data(cv_data.data, unique_id)
            return send_from_directory(
                app.config['PDF_OUTPUT_FOLDER'], 
                pdf_filename, 
                as_attachment=True,
                download_name=f"{current_user.username}_cv.pdf"
            )
        except Exception as e:
            # flash(f"Error generating PDF: {str(e)}")
            return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")

    def generate_pdf_from_data(cv_data, unique_id):
        """Generate PDF from CV data dictionary"""
        # Create a temporary JSON file
        temp_json = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{unique_id}.json")
        with open(temp_json, 'w') as f:
            json.dump(cv_data, f)
        
        # Generate PDF
        pdf_filename = generate_pdf(temp_json, unique_id)
        
        # Remove temporary file
        os.remove(temp_json)
        
        return pdf_filename

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Scheduled cleanup
    @app.before_request
    def scheduled_cleanup():
        if request.endpoint != 'static':
            for folder in [app.config['UPLOAD_FOLDER'], app.config['LATEX_OUTPUT_FOLDER']]:
                cleanup_old_files(folder, days=1)

    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')