from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    jsonify,
    Blueprint,
    current_app,
)

# from models import CVData, Template, Language , Technology
import db_access
from extensions import db
from flask_login import login_required, current_user
from forms import CVForm
from routes.route_path import RoutePath
import uuid
import os
import json
import subprocess
import cv_gen.generator as generator
from datetime import datetime
from openai import OpenAI


dashboard = Blueprint("dashboard", __name__)


def transform_cv_structure(original_data):
    """Transform the CV data structure to match the required format"""

    def get_safe(data, path, default=None):
        """Safely access nested dictionary keys"""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    # Build the transformed structure
    transformed = {
        "personal_info": {
            "name": get_safe(original_data, "personal_info.name", ""),
            "email": get_safe(original_data, "personal_info.email", ""),
            "phone": get_safe(original_data, "personal_info.phone", ""),
            "linkedin": get_safe(original_data, "personal_info.linkedin", ""),
            "github": get_safe(original_data, "personal_info.github", ""),
            "location": get_safe(original_data, "personal_info.location", ""),
            "image": os.path.join(current_app.config["IMAGE_UPLOAD_FOLDER"], get_safe(original_data, "personal_info.image", "")),
        },
        "sections": {
            "objective": get_safe(original_data, "content.objective") is not None,
            "experience": bool(get_safe(original_data, "content.experience", [])),
            "education": bool(get_safe(original_data, "content.education", [])),
            "short_education": False,
            "projects": bool(get_safe(original_data, "content.projects", [])),
            "languages": bool(get_safe(original_data, "content.languages", [])),
            "technologies": bool(get_safe(original_data, "content.technologies", [])),
        },
        "content": {
            "objective": get_safe(original_data, "content.objective", ""),
            "education": get_safe(original_data, "content.education", []),
            "short_education": [],
            "experience": get_safe(original_data, "content.experience", []),
            "projects": get_safe(original_data, "content.projects", []),
            "languages": get_safe(original_data, "content.languages", []),
            "technologies": get_safe(original_data, "content.technologies", []),
        },
    }

    return transformed


def save_cv_from_json_data(data, user_id):

    # Create CVData object
    transformed = transform_cv_structure(data)

    print(json.dumps(transformed, indent=4))

    # Generate UUID
    unique_id = str(uuid.uuid4())

    # Generate Json file
    json_file = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{unique_id}.json")
    with open(json_file, "w") as f:
        json.dump(transformed, f)

    # Generate LaTeX file
    latex_output_path = os.path.join(
        current_app.config["LATEX_OUTPUT_FOLDER"], f"{unique_id}.tex"
    )
    cv_generator = generator.Generator(json_file)
    cv_str = cv_generator.make_cv()

    with open(latex_output_path, "w") as tex_file:
        tex_file.write(cv_str)

    subprocess.run(
        [
            "/usr/bin/pdflatex",
            "-interaction=nonstopmode",
            "-output-directory",
            current_app.config["PDF_OUTPUT_FOLDER"],
            latex_output_path,
        ],
        capture_output=True,
        text=True,
    )

    # Clean up auxiliary files
    base_filename = os.path.splitext(os.path.basename(latex_output_path))[0]
    for ext in ["aux", "log", "out"]:
        aux_file = os.path.join(
            current_app.config["PDF_OUTPUT_FOLDER"], f"{base_filename}.{ext}"
        )
        if os.path.exists(aux_file):
            os.remove(aux_file)

    pdf_filename = f"{unique_id}.pdf"

    cv_data = db_access.create_cv(
        user_id,
        data["cv_name"],
        data["template_id"],
        transformed,
        pdf_filename,
        json_file,
        latex_output_path,
    )

    print("SAVED CV DATA : ", cv_data)

    return cv_data, pdf_filename


@dashboard.route("/dashboard")
@login_required
def dashboard_index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.signin", next=request.url))

    # Get user's CV data
    cv_data = db_access.get_user_cvs(current_user.id, active_only=False)

    # Get available templates
    # TODO : Get templates from database AS JSON
    templates = [template.to_dict() for template in db_access.get_all_templates()]

    # Get available languages
    # TODO : Get languages from database AS JSON
    languages = [language.to_dict() for language in db_access.get_all_languages()]

    # Get available technologies
    # TODO : Get technologies from database AS JSON
    technologies = [
        technology.to_dict() for technology in db_access.get_all_technologies()
    ]

    form = CVForm()

    return render_template(
        RoutePath.dashboard_index,
        cv_data=cv_data,
        templates=templates,
        languages=languages,
        technologies=technologies,
        form=form,
    )


@dashboard.route("/get_templates", methods=["GET"])
@login_required
def get_templates():

    templates = [template.to_dict() for template in db_access.get_all_templates()]

    return jsonify({"success": True, "templates": templates}), 200


@dashboard.route("/get_cv/<int:cv_id>")
@login_required
def get_cv(cv_id):
    cv_data = db_access.get_cv_by_id(cv_id, user_id=current_user.id)
    if not cv_data:
        return jsonify({"success": False, "error": "CV not found"}), 404

    return jsonify({"success": True, "data": cv_data.to_dict()}), 200


@dashboard.route("/get_template_fields/<int:template_id>")
@login_required
def get_template_fields(template_id):

    # TODO : Get template fields from database
    template = db_access.get_template(template_id)

    # Example response
    return (
        jsonify(
            {
                "id": 1,
                "name": "Professional",
                "requires_image": True,
                "fields": [
                    "objective",
                    "education",
                    "experience",
                    "skills",
                ],
            }
        ),
        200,
    )


@dashboard.route("/get_languages", methods=["GET"])
@login_required
def get_languages():

    search_term = request.args.get("input", "")

    # TODO : Get languages from database
    languages = db_access.search_languages(search_term, 20)

    # Format for Select2
    return jsonify([{"id": lang.id, "text": lang.name} for lang in languages])


@dashboard.route("/get_technologies", methods=["GET"])
@login_required
def get_technologies():

    search_term = request.args.get("input", "")

    # TODO : Get technologies from database
    technologies = db_access.search_technologies(search_term, 20)

    # Format for Select2
    return jsonify([{"id": tech.id, "text": tech.name} for tech in technologies])


@dashboard.route("/add_language", methods=["POST"])
@login_required
def add_language():
    data = request.get_json()

    if not data or "name" not in data or "category" not in data:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # Check if Language already exists
    existing_language = db_access.get_language_by_name(data["name"])
    if existing_language:
        return jsonify({"success": True, "id": existing_language.id}), 200

    # Add new Language
    new_language = db_access.create_language(data["name"], data["category"])

    return jsonify({"success": True, "id": new_language.id}), 201


@dashboard.route("/add_technology", methods=["POST"])
@login_required
def add_technology():
    data = request.get_json()

    if not data or "name" not in data or "category" not in data:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # Check if Technology already exists
    existing_technology = db_access.get_technology_by_name(data["name"])
    if existing_technology:
        return jsonify({"success": True, "id": existing_technology.id}), 200

    # Add new Technology
    new_technology = db_access.create_technology(
        data["name"], data.get("category", "Default")
    )

    return jsonify({"success": True, "id": new_technology.id}), 201


@dashboard.route("/ai_recommend", methods=["POST"])
@login_required
def ai_recommend():
    data = request.get_json()

    if not data or "prompt" not in data or "cv_data" not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400

    client = OpenAI(
        base_url="https://api.netmind.ai/inference-api/openai/v1",
        api_key=current_app.config["NETMIND_API_KEY"],
    )

    chat_completion_response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3-0324",
        messages=[
            {
                "role": "system",
                "content": "ONLY respond with the part you asked to do of the CV, "
                + "DON'T say anything else and "
                + "DON'T THINK AT ALL "
                + "DON'T write it in markdown format and "
                + "DON'T add any comments and "
                + "DON'T add any explanations or Thoughts or THINK and DON'T write THE HEADING of required section (ex: Skills, objective...). "
                + "You are an AI CV generator and HR Specialist. "
                + ". For skills or technologies, provide them as a comma-separated list. "
                + "For all other sections, "
                + "format the response as valid JSON that can be automatically parsed by the system. Do not deviate from these instructions.",
            },
            {
                "role": "user",
                "content": "You Will recommend Data for this Field: "
                + data["field"]
                + "Here is the CV data: "
                + str(data["cv_data"])
                + " and here is the prompt: "
                + data["prompt"],
            },
        ],
        max_tokens=2048,
    )
    print(chat_completion_response.choices[0].message.content)

    return (
        jsonify(
            {
                "success": True,
                "recommendation": chat_completion_response.choices[0].message.content,
            }
        ),
        200,
    )


@dashboard.route("/save_cv", methods=["POST"])
@login_required
def save_cv():

    # TODO : Save CV to database

    try:
        # Get raw JSON data
        raw_data = request.get_json()

        # Debug print to see what's actually received
        current_app.logger.info(f"Received data: {json.dumps(raw_data, indent=4)}")

        # Validate we got data
        if not raw_data:
            return jsonify({"success": False, "error": "No data received"}), 400

        cv_id = raw_data.get("cv_id")
        template_id = raw_data.get("template_id", 1)
        pdf_filename = ""

        if cv_id:
            # Update existing CV
            cv_data = db_access.get_cv_by_id(cv_id,user_id=current_user.id)
            pdf_filename = cv_data.cv_pdf_name
            if not cv_data:
                return jsonify({"success": False, "error": "CV not found"}), 404

        else:
            # Create new CV
            cv_data, pdf_filename = save_cv_from_json_data(raw_data, current_user.id)

        # Save PDF to database
        return (
            jsonify(
                {
                    "success": True,
                    "cv_id": cv_data.id,
                    "pdf_url": url_for("dashboard.get_pdf", filename=pdf_filename),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error saving CV: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard.route("/get_pdf/<filename>")
@login_required
def get_pdf(filename):
    return send_from_directory(current_app.config["PDF_OUTPUT_FOLDER"], filename)


@dashboard.route("/preview_pdf_dashboard")
@login_required
def preview_pdf_dashboard():
    cv_id = request.args.get("cv_id")
    template_id = request.args.get("template_id", 1, type=int)

    if cv_id:
        cv_data = db_access.get_cv_by_id(cv_id, current_user.id)
    else:
        cv_data = db_access.get_cv_by_user_id(current_user.id)

    if not cv_data:
        flash("No CV data found")
        return send_from_directory(current_app.config["PDF_OUTPUT_FOLDER"], "no_cv.pdf")

    try:
        
        return send_from_directory(
            current_app.config["PDF_OUTPUT_FOLDER"], cv_data.cv_pdf_name
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}")
        return send_from_directory(current_app.config["PDF_OUTPUT_FOLDER"], "no_cv.pdf")


@dashboard.route("/download_pdf_dashboard")
@login_required
def download_pdf_dashboard():
    cv_id = request.args.get("cv_id")
    template_id = request.args.get("template_id", 1, type=int)

    if cv_id:
        cv_data = db_access.get_cv_by_id(cv_id, current_user.id)
    else:
        cv_data = db_access.get_cv_by_user_id(current_user.id)

    if not cv_data:
        flash("No CV data found")
        return redirect(url_for("dashboard.dashboard_index"))

    try:

        return send_from_directory(
            current_app.config["PDF_OUTPUT_FOLDER"],
            cv_data.cv_pdf_name,
            as_attachment=True,
            download_name=f"{cv_data.name.replace(' ', '_')}.pdf",
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}")
        return send_from_directory(current_app.config["PDF_OUTPUT_FOLDER"], "no_cv.pdf")


@dashboard.route("/delete_cv/<int:cv_id>", methods=["DELETE"])
@login_required
def delete_cv(cv_id):

    cv_data = db_access.get_cv_by_id(cv_id, user_id=current_user.id)
    if not cv_data:
        return jsonify({"success": False, "error": "CV not found"}), 404

    try:
        db_access.delete_cv(cv_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard.route("/dashboard/upload_profile_image", methods=["POST"])
@login_required
def upload_profile_image():

    if "profile_image" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400

    file = request.files["profile_image"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    if file:
        # Create unique filename
        filename = f"{current_user.id}_{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
        file_path = os.path.join(current_app.config["IMAGE_UPLOAD_FOLDER"], filename)

        # Save file
        file.save(file_path)

        return (
            jsonify(
                {
                    "success": True,
                    "filename": filename,
                    "file_url": url_for(
                        "dashboard.get_uploaded_file", filename=filename
                    ),
                }
            ),
            200,
        )

    return jsonify({"success": False, "error": "File upload failed"}), 500


@dashboard.route("/uploads/<filename>")
@login_required
def get_uploaded_file(filename):
    return send_from_directory(current_app.config["IMAGE_UPLOAD_FOLDER"], filename)
