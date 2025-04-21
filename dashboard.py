from flask import (
    render_template, request, redirect, url_for, 
    flash, send_from_directory, jsonify, Blueprint,
    current_app  # <-- Replaced 'app' import
)
from models import CVData
from extensions import db
from flask_login import login_required, current_user
from forms import CVForm
from routes.route_path import RoutePath
import uuid
import os
import json
import subprocess
import cv_gen.generator as generator

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def dashboard_index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.signin'))
    
    cv_data = CVData.query.filter_by(user_id=current_user.id).first()
    form = CVForm()
    return render_template(
        RoutePath.dashboard_index, 
        cv_data=cv_data.data if cv_data else None,
        form=form
    )

def generate_pdf(input_path, unique_id):
    """Helper function to generate PDF from input file"""
    latex_output_path = os.path.join(
        current_app.config['LATEX_OUTPUT_FOLDER'], 
        f"{unique_id}.tex"
    )
    pdf_filename = f"{unique_id}.pdf"
    pdf_output_path = os.path.join(
        current_app.config['PDF_OUTPUT_FOLDER'],
        pdf_filename
    )
    cv_generator = generator.Generator(input_path)
    cv_str = cv_generator.make_cv()
    
    with open(latex_output_path, "w") as tex_file:
        tex_file.write(cv_str)
    
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-output-directory", 
        current_app.config['PDF_OUTPUT_FOLDER'], latex_output_path], 
        capture_output=True,
        text=True
    )
    
    # Clean up auxiliary files
    base_filename = os.path.splitext(os.path.basename(latex_output_path))[0]
    for ext in ['aux', 'log', 'out']:
        aux_file = os.path.join(
            current_app.config['PDF_OUTPUT_FOLDER'], 
            f"{base_filename}.{ext}"
        )
        if os.path.exists(aux_file):
            os.remove(aux_file)
    
    return pdf_filename

def generate_pdf_from_data(cv_data, unique_id):
    """Generate PDF from CV data dictionary"""
    # Create a temporary JSON file
    temp_json = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{unique_id}.json")
    with open(temp_json, 'w') as f:
        json.dump(cv_data, f)
    
    # Generate PDF
    pdf_filename = generate_pdf(temp_json, unique_id)
    
    # Remove temporary file
    os.remove(temp_json)
    
    return pdf_filename

@dashboard.route('/save_cv', methods=['POST'])
@login_required
def save_cv():
    try:
        # Get raw JSON data
        raw_data = request.get_json()
        
        # Debug print to see what's actually received
        current_app.logger.debug(f"Received data: {raw_data}")
        
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
        current_app.logger.error(f"Error saving CV: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e),
            'received_data': raw_data  # For debugging
        }), 500

@dashboard.route('/preview_pdf_dashboard')
@login_required
def preview_pdf_dashboard():
    cv_data = CVData.query.filter_by(user_id=current_user.id).first()
    print("cv_data", cv_data)
    if not cv_data:
        flash("No CV data found")
        send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")
    
    try:
        unique_id = uuid.uuid4()
        pdf_filename = generate_pdf_from_data(cv_data.data, unique_id)
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}")
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")

@dashboard.route('/download_pdf_dashboard')
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
            current_app.config['PDF_OUTPUT_FOLDER'], 
            pdf_filename, 
            as_attachment=True,
            download_name=f"{current_user.username}_cv.pdf"
        )
    except Exception as e:
        # flash(f"Error generating PDF: {str(e)}")
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")
