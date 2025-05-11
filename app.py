import os
import uuid
import json
import subprocess
from datetime import datetime, timedelta
from flask import Flask, request, render_template, url_for, send_from_directory, flash, jsonify , send_file ,make_response
from werkzeug.utils import secure_filename
import cv_gen.generator as generator
from models import User, CVData, ContactMessage
from auth import auth as auth_blueprint
from extensions import db, login_manager,get_celery ,get_limiter , init_app
from forms import CVForm
from functools import wraps
import os
from flask import Flask
from routes.route_path import RoutePath , routes as routes_blueprint
from dashboard import dashboard





def create_app():
    
    # Initialize Flask app
    app = Flask(__name__)
    

    # Initialize extensions
    init_app(app) 

    # Configure Celery if available
    celery = get_celery(app)

    limiter = get_limiter(app)

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

    # Add this helper function to check allowed image types
    def allowed_image_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
    

    # Routes
    @app.route('/')
    def index():
        return render_template( RoutePath.home_index )


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
        
        # Handle image upload if provided

        try : 
            profile_image = None
            image_path = None

            if 'profile_image' in request.files:

                app.logger.info("Profile image Found in request")

                profile_image = request.files['profile_image']

                if profile_image and allowed_image_file(profile_image.filename):

                    app.logger.info("Profile image uploaded successfully")

                    # Save the image with unique ID
                    unique_id = uuid.uuid4()
                    image_filename = f"{unique_id}_{secure_filename(profile_image.filename)}"
                    image_path = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], image_filename)

                    # Save the image
                    app.logger.info(f"Image saved to: {image_path}")
                    profile_image.save(image_path)
                
        except Exception as e:
            app.logger.info("Profile image upload failed with error:" + str(e))

                
        
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
                
                
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                latex_output_path = os.path.join(app.config['LATEX_OUTPUT_FOLDER'], f"{unique_id}.tex")
                pdf_filename = f"{unique_id}.pdf"
                pdf_output_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
                
                app.logger.info(f"File paths configured - "
                            f"Input: {input_path}, "
                            f"LaTeX Output: {latex_output_path}, "
                            f"PDF Output: {pdf_output_path}"
                            f"Profile Image: {image_path}"
                            )
                
                
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

                cv_generator = None

                try : 

                    if image_path is not None:

                        cv_generator = generator.Generator(input_path, template=template_style, image_path=image_path)
                    else:
                        cv_generator = generator.Generator(input_path, template=template_style)

                except Exception as e:
                    app.logger.error(f"Failed to generate CV with selected template: {str(e)}", exc_info=True)

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
                        ["/usr/bin/pdflatex", "-interaction=nonstopmode", "-output-directory", app.config['PDF_OUTPUT_FOLDER'], latex_output_path],
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
            ["/usr/bin/pdflatex", "-interaction=nonstopmode", "-output-directory", 
            app.config['PDF_OUTPUT_FOLDER'] , latex_output_path],
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
        try:
            # Security checks
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'

            pdf_path = os.path.join(os.path.abspath(app.config['PDF_OUTPUT_FOLDER']), filename)

            if not os.path.exists(pdf_path):
                app.logger.error(f"Download failed - file not found: {pdf_path}")
                return page_not_found("Download failed - File not found")

            app.logger.info(f"Serving download for: {pdf_path}")
            return send_from_directory(
                app.config['PDF_OUTPUT_FOLDER'],
                filename,
                as_attachment=True,
                mimetype='application/pdf'
            )

        except Exception as e:
            app.logger.error(f"Download failed: {str(e)}", exc_info=True)
            return internal_server_error(e)


    @app.route('/preview/<filename>')
    def preview_pdf(filename):
        app.logger.info(f"Received preview request for {filename}")
        try:
            # Ensure filename has .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'

            # Construct full safe path
            pdf_dir = os.path.abspath(app.config['PDF_OUTPUT_FOLDER'])
            pdf_path = os.path.join(pdf_dir, filename)

            app.logger.info(f"Previewing PDF: {pdf_path}")
            app.logger.info(f"PDF directory: {pdf_dir}")

            # Security checks
            if not os.path.exists(pdf_path):
                app.logger.error(f"Preview failed - file not found: {pdf_path}")
                return page_not_found("Preview failed - File not found")
                

            if not pdf_path.startswith(pdf_dir):
                app.logger.error(f"Security violation: {pdf_path} outside allowed directory")
                return page_not_found("Security violation")

            app.logger.info(f"Serving PDF preview: {pdf_path}")

            # Serve with correct headers
            response = send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=False,
                conditional=True
            )

            # Cache control headers
            response.headers['Cache-Control'] = 'no-store, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            return response

        except Exception as e:
            app.logger.error(f"Preview failed: {str(e)}", exc_info=True)
            return internal_server_error(e)


    @app.route('/sample-json')
    def sample_json():
        """Return a sample JSON structure for CV creation"""
        return send_from_directory(
            app.config['MOCK_FOLDER'],
            'mock.json',
            as_attachment=True,
            mimetype='application/json'
        )


    # Text file download endpoint
    @app.route('/samples/txt-sample-file')
    def txt_file():
        filename = 'mock.txt'
        return send_from_directory(
            app.config['MOCK_FOLDER'],
            filename,
            as_attachment=True,
            mimetype='text/plain'
        )

    # JSON file download endpoint
    @app.route('/samples/json-sample-file')
    def json_file():
        filename = 'mock.json'
        return send_from_directory(
            app.config['MOCK_FOLDER'],
            filename,
            as_attachment=True,
            mimetype='application/json'
        )

    # DOCX file download endpoint
    @app.route('/samples/docx-sample-file')
    def docx_file():
        filename = 'mock.docx'
        return send_from_directory(
            app.config['MOCK_FOLDER'],
            filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    

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


    @app.route('/how-to-use/intro-vid', methods=['GET'])
    def intro_video():
        # Send the intro video
        return send_file(
            os.path.join(app.root_path, 'static', 'videos', 'intro-vid.mp4'),
            mimetype='video/mp4',
            as_attachment=False,
            conditional=True
        )

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
