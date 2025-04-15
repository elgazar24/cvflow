import os
import uuid
import json
import subprocess
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
import cv_gen.generator as generator

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# Folder configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LATEX_OUTPUT_FOLDER'] = 'latex_outputs'
app.config['PDF_OUTPUT_FOLDER'] = 'pdf_outputs'
app.config['ALLOWED_EXTENSIONS'] = {'json', 'txt'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LATEX_OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
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
    
    return render_template('index.html')

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
def contact():
    """Handle contact form submissions"""
    if request.method == 'POST':
        # You would normally process the form data and send an email here
        # For this example, we'll just return a success message
        data = request.get_json()
        
        # Simple validation
        if not all(key in data for key in ['name', 'email', 'message']):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Here you would send an email with the contact form data
        # For now, we'll just log it
        app.logger.info(f"Contact form submission: {data}")
        
        return jsonify({'success': True, 'message': 'Message received! Thank you for your feedback.'})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)