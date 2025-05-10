from flask import (
    render_template, request, redirect, url_for, 
    flash, send_from_directory, jsonify, Blueprint,
    current_app
)
from models import CVData, Template, Skill
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
    
    # Get user's CV data
    cv_data = CVData.query.filter_by(user_id=current_user.id).all()
    
    # Get available templates
    templates = Template.query.all()
    
    # Get available skills
    skills = Skill.query.all()
    
    form = CVForm()
    return render_template(
        RoutePath.dashboard_index, 
        cv_data=cv_data,
        templates=templates,
        skills=skills,
        form=form
    )

@dashboard.route('/get_templates', methods=['POST'])
@login_required
def get_templates():

    return jsonify({'success': True, 'templates': [{'id': 1, 'name': 'Default' , 'requires_image': True} , {'id': 2, 'name': 'Professional' , 'requires_image': True}]}), 200

@dashboard.route('/get_cv/<int:cv_id>')
@login_required
def get_cv(cv_id):
    cv_data = CVData.query.filter_by(id=cv_id, user_id=current_user.id).first()
    if not cv_data:
        return jsonify({'success': False, 'error': 'CV not found'}), 404
    
    return jsonify({'success': True, 'data': cv_data.data}), 200

@dashboard.route('/get_template_fields/<int:template_id>')
@login_required
def get_template_fields(template_id):
    template = Template.query.get(template_id)
    if not template:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    
    # Return template fields and requirements
    return jsonify({
        'success': True, 
        'template_name': template.name,
        'fields': template.fields,
        'requires_image': template.requires_image
    }), 200


@dashboard.route('/get_skills')
@login_required
def get_skills():
    skills = Skill.query.all()
    print(skills)
    return jsonify({
        'success': True,
        'skills': [{'id': skill.id, 'name': skill.name, 'category': skill.category} for skill in skills]
    }), 200

@dashboard.route('/add_skill', methods=['POST'])
@login_required
def add_skill():
    data = request.get_json()
    
    if not data or 'name' not in data or 'category' not in data:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Check if skill already exists
    existing_skill = Skill.query.filter_by(name=data['name']).first()
    if existing_skill:
        return jsonify({'success': True, 'id': existing_skill.id}), 200
    
    # Add new skill
    new_skill = Skill(name=data['name'], category=data['category'])
    db.session.add(new_skill)
    db.session.commit()
    
    return jsonify({'success': True, 'id': new_skill.id}), 201

@dashboard.route('/ai_recommend', methods=['POST'])
@login_required
def ai_recommend():
    data = request.get_json()
    
    if not data or 'prompt' not in data or 'cv_data' not in data:
        return jsonify({'success': False, 'error': 'Missing required data'}), 400
    
    # This will be implemented later to call AI service
    # For now, return empty response
    return jsonify({'success': True, 'recommendation': ''}), 200

def generate_pdf(input_path, unique_id, template_id=1):
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
    
    # Get template configuration
    template = Template.query.get(template_id)
    template_config = template.config if template else {}
    
    cv_generator = generator.Generator(input_path, template_config)
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

def generate_pdf_from_data(cv_data, unique_id, template_id=1):
    """Generate PDF from CV data dictionary"""
    # Create a temporary JSON file
    temp_json = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{unique_id}.json")
    with open(temp_json, 'w') as f:
        json.dump(cv_data, f)
    
    # Generate PDF
    pdf_filename = generate_pdf(temp_json, unique_id, template_id)
    
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
        
        cv_id = raw_data.get('cv_id')
        cv_name = raw_data.get('cv_name', 'Untitled CV')
        template_id = raw_data.get('template_id', 1)
        
        # Remove metadata fields from the data before storing
        cv_content = {k: v for k, v in raw_data.items() 
                     if k not in ['cv_id', 'cv_name', 'template_id']}
        
        if cv_id:
            # Update existing CV
            cv_data = CVData.query.filter_by(id=cv_id, user_id=current_user.id).first()
            if not cv_data:
                return jsonify({'success': False, 'error': 'CV not found'}), 404
            cv_data.name = cv_name
            cv_data.template_id = template_id
            cv_data.data = cv_content
        else:
            # Create new CV
            cv_data = CVData(
                user_id=current_user.id,
                name=cv_name,
                template_id=template_id,
                data=cv_content
            )
            db.session.add(cv_data)
        
        db.session.commit()
        
        # Generate a unique ID for the PDF
        unique_id = uuid.uuid4()
        
        # Generate PDF preview
        pdf_filename = generate_pdf_from_data(cv_content, unique_id, template_id)
        
        return jsonify({
            'success': True,
            'cv_id': cv_data.id,
            'pdf_url': url_for('dashboard.get_pdf', filename=pdf_filename)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error saving CV: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@dashboard.route('/get_pdf/<filename>')
@login_required
def get_pdf(filename):
    return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], filename)

@dashboard.route('/preview_pdf_dashboard')
@login_required
def preview_pdf_dashboard():
    cv_id = request.args.get('cv_id')
    template_id = request.args.get('template_id', 1, type=int)
    
    if cv_id:
        cv_data = CVData.query.filter_by(id=cv_id, user_id=current_user.id).first()
    else:
        cv_data = CVData.query.filter_by(user_id=current_user.id).first()
    
    if not cv_data:
        flash("No CV data found")
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")
    
    try:
        unique_id = uuid.uuid4()
        pdf_filename = generate_pdf_from_data(cv_data.data, unique_id, template_id)
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}")
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")

@dashboard.route('/download_pdf_dashboard')
@login_required
def download_pdf_dashboard():
    cv_id = request.args.get('cv_id')
    template_id = request.args.get('template_id', 1, type=int)
    
    if cv_id:
        cv_data = CVData.query.filter_by(id=cv_id, user_id=current_user.id).first()
    else:
        cv_data = CVData.query.filter_by(user_id=current_user.id).first()
    
    if not cv_data:
        flash("No CV data found")
        return redirect(url_for('dashboard.dashboard_index'))
    
    try:
        unique_id = uuid.uuid4()
        pdf_filename = generate_pdf_from_data(cv_data.data, unique_id, template_id)
        return send_from_directory(
            current_app.config['PDF_OUTPUT_FOLDER'], 
            pdf_filename, 
            as_attachment=True,
            download_name=f"{cv_data.name.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}")
        return send_from_directory(current_app.config['PDF_OUTPUT_FOLDER'], "no_cv.pdf")

@dashboard.route('/delete_cv/<int:cv_id>', methods=['DELETE'])
@login_required
def delete_cv(cv_id):
    cv_data = CVData.query.filter_by(id=cv_id, user_id=current_user.id).first()
    if not cv_data:
        return jsonify({'success': False, 'error': 'CV not found'}), 404
    
    try:
        db.session.delete(cv_data)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard.route('/dashboard/upload_profile_image', methods=['POST'])
@login_required
def upload_profile_image():

    if 'profile_image' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    file = request.files['profile_image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    
    if file:
        # Create unique filename
        filename = f"{current_user.id}_{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
        file_path = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_url': url_for('dashboard.get_uploaded_file', filename=filename)
        }), 200
    
    return jsonify({'success': False, 'error': 'File upload failed'}), 500

@dashboard.route('/uploads/<filename>')
@login_required
def get_uploaded_file(filename):
    return send_from_directory(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)