from extensions import db
from models import (
    User, CVData, PersonalInfo, Objective, Education, EducationCoursework, 
    Experience, ExperienceResponsibility, Project, ProjectResponsibility, 
    Certification, Interest, Reference, Achievement, Publication, CustomField,
    Language, Technology, CVLanguage, CVTechnology, Template, ComponentLibrary,
    ContactMessage
)
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from datetime import datetime
import json

# ------------------- User Management Functions -------------------

def create_user(username, email, password):
    """Create a new user"""
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError:
        db.session.rollback()
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    return User.query.get(user_id)

def get_user_by_username(username):
    """Get user by username"""
    return User.query.filter_by(username=username).first()

def get_user_by_email(email):
    """Get user by email"""
    return User.query.filter_by(email=email).first()

def update_user(user_id, username=None, email=None):
    """Update user information"""
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    if username:
        user.username = username
    if email:
        user.email = email
    
    try:
        db.session.commit()
        return user
    except IntegrityError:
        db.session.rollback()
        return None

def change_password(user_id, new_password):
    """Change user password"""
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    user.set_password(new_password)
    db.session.commit()
    return True

# ------------------- CV Management Functions -------------------

def create_cv(user_id, name, template_id, data, pdf_name=None, json_name=None, latex_name=None):
    """Create a new CV"""
    cv = CVData(
        user_id=user_id,
        name=name,
        template_id=template_id,
        cv_pdf_name=pdf_name,
        cv_json_name=json_name,
        cv_latex_name=latex_name,
        data=data
    )
    db.session.add(cv)
    db.session.commit()
    return cv

def get_cv_by_id(cv_id , user_id=None):
    """Get CV by ID"""
    cv_data = CVData.query.get(cv_id)
    
    if user_id and cv_data.user_id != user_id:
        return None
    return cv_data

def get_user_cvs(user_id, active_only=True):
    """Get all CVs for a specific user"""
    query = CVData.query.filter_by(user_id=user_id)
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(CVData.last_updated.desc()).all()

def update_cv(cv_id, name=None, template_id=None, is_active=None, data=None):
    """Update CV information"""
    cv = get_cv_by_id(cv_id)
    if not cv:
        return None
    
    if name:
        cv.name = name
    if template_id:
        cv.template_id = template_id
    if is_active is not None:
        cv.is_active = is_active
    if data:
        cv.data = data
    
    cv.last_updated = datetime.utcnow()
    db.session.commit()
    return cv

def delete_cv(cv_id):
    """Delete a CV"""
    cv = get_cv_by_id(cv_id)
    if not cv:
        return False
    
    db.session.delete(cv)
    db.session.commit()
    return True

def duplicate_cv(cv_id, new_name=None):
    """Duplicate a CV with all its components"""
    original_cv = get_cv_by_id(cv_id)
    if not original_cv:
        return None
    
    # Create new CV
    new_cv = CVData(
        user_id=original_cv.user_id,
        name=new_name or f"{original_cv.name} (Copy)",
        template_id=original_cv.template_id,
        data=original_cv.data
    )
    db.session.add(new_cv)
    db.session.flush()  # Get the new CV ID without committing
    
    # Duplicate personal info
    if original_cv.personal_info:
        personal_info = original_cv.personal_info
        new_personal_info = PersonalInfo(
            cv_id=new_cv.id,
            name=personal_info.name,
            email=personal_info.email,
            phone=personal_info.phone,
            linkedin=personal_info.linkedin,
            github=personal_info.github,
            location=personal_info.location,
            image=personal_info.image,
            website=personal_info.website
        )
        db.session.add(new_personal_info)
    
    # Duplicate objectives
    for obj in original_cv.objectives:
        new_obj = Objective(
            cv_id=new_cv.id,
            content=obj.content,
            job_title=obj.job_title
        )
        db.session.add(new_obj)
    
    # Duplicate educations with coursework
    for edu in original_cv.educations:
        new_edu = Education(
            cv_id=new_cv.id,
            degree=edu.degree,
            university=edu.university,
            start_date=edu.start_date,
            end_date=edu.end_date,
            gpa=edu.gpa,
            certificate=edu.certificate,
            location=edu.location
        )
        db.session.add(new_edu)
        db.session.flush()
        
        for course in edu.coursework:
            new_course = EducationCoursework(
                education_id=new_edu.id,
                course=course.course,
                order=course.order
            )
            db.session.add(new_course)
    
    # Duplicate experiences with responsibilities
    for exp in original_cv.experiences:
        new_exp = Experience(
            cv_id=new_cv.id,
            role=exp.role,
            company=exp.company,
            location=exp.location,
            start_date=exp.start_date,
            end_date=exp.end_date
        )
        db.session.add(new_exp)
        db.session.flush()
        
        for resp in exp.responsibilities:
            new_resp = ExperienceResponsibility(
                experience_id=new_exp.id,
                description=resp.description,
                order=resp.order
            )
            db.session.add(new_resp)
    
    # Duplicate projects with responsibilities
    for proj in original_cv.projects:
        new_proj = Project(
            cv_id=new_cv.id,
            title=proj.title,
            description=proj.description,
            github_link=proj.github_link,
            live_link=proj.live_link,
            start_date=proj.start_date,
            end_date=proj.end_date
        )
        db.session.add(new_proj)
        db.session.flush()
        
        for resp in proj.responsibilities:
            new_resp = ProjectResponsibility(
                project_id=new_proj.id,
                description=resp.description,
                order=resp.order
            )
            db.session.add(new_resp)
    
    # Duplicate certifications
    for cert in original_cv.certifications:
        new_cert = Certification(
            cv_id=new_cv.id,
            name=cert.name,
            issuer=cert.issuer,
            date=cert.date,
            url=cert.url,
            description=cert.description
        )
        db.session.add(new_cert)
    
    # Duplicate interests
    for interest in original_cv.interests:
        new_interest = Interest(
            cv_id=new_cv.id,
            name=interest.name,
            description=interest.description
        )
        db.session.add(new_interest)
    
    # Duplicate references
    for ref in original_cv.references:
        new_ref = Reference(
            cv_id=new_cv.id,
            name=ref.name,
            position=ref.position,
            company=ref.company,
            email=ref.email,
            phone=ref.phone,
            relationship=ref.relationship
        )
        db.session.add(new_ref)
    
    # Duplicate achievements
    for achievement in original_cv.achievements:
        new_achievement = Achievement(
            cv_id=new_cv.id,
            title=achievement.title,
            description=achievement.description,
            date=achievement.date
        )
        db.session.add(new_achievement)
    
    # Duplicate publications
    for pub in original_cv.publications:
        new_pub = Publication(
            cv_id=new_cv.id,
            title=pub.title,
            publisher=pub.publisher,
            authors=pub.authors,
            publication_date=pub.publication_date,
            url=pub.url,
            description=pub.description
        )
        db.session.add(new_pub)
    
    # Duplicate custom fields
    for custom in original_cv.custom_fields:
        new_custom = CustomField(
            cv_id=new_cv.id,
            field_name=custom.field_name,
            field_value=custom.field_value,
            field_type=custom.field_type,
            order=custom.order
        )
        db.session.add(new_custom)
    
    # Duplicate languages
    for cv_lang in original_cv.cv_languages:
        new_cv_lang = CVLanguage(
            cv_id=new_cv.id,
            language_id=cv_lang.language_id,
            level=cv_lang.level
        )
        db.session.add(new_cv_lang)
    
    # Duplicate technologies
    for cv_tech in original_cv.cv_technologies:
        new_cv_tech = CVTechnology(
            cv_id=new_cv.id,
            technology_id=cv_tech.technology_id,
            level=cv_tech.level
        )
        db.session.add(new_cv_tech)
    
    db.session.commit()
    return new_cv

def update_cv_json_data(cv_id):
    """Update CV's consolidated JSON data"""
    cv = get_cv_by_id(cv_id)
    if not cv:
        return False
    
    # Build the JSON data structure
    data = {}
    
    # Personal Info
    if cv.personal_info:
        data['personal_info'] = {
            'name': cv.personal_info.name,
            'email': cv.personal_info.email,
            'phone': cv.personal_info.phone,
            'linkedin': cv.personal_info.linkedin,
            'github': cv.personal_info.github,
            'location': cv.personal_info.location,
            'image': cv.personal_info.image,
            'website': cv.personal_info.website
        }
    
    # Objectives
    data['objectives'] = []
    for obj in cv.objectives:
        data['objectives'].append({
            'id': obj.id,
            'content': obj.content,
            'job_title': obj.job_title
        })
    
    # Education
    data['education'] = []
    for edu in cv.educations:
        edu_data = {
            'id': edu.id,
            'degree': edu.degree,
            'university': edu.university,
            'start_date': edu.start_date,
            'end_date': edu.end_date,
            'gpa': edu.gpa,
            'certificate': edu.certificate,
            'location': edu.location,
            'coursework': []
        }
        
        for course in edu.coursework:
            edu_data['coursework'].append({
                'id': course.id,
                'course': course.course,
                'order': course.order
            })
        
        data['education'].append(edu_data)
    
    # Experience
    data['experience'] = []
    for exp in cv.experiences:
        exp_data = {
            'id': exp.id,
            'role': exp.role,
            'company': exp.company,
            'location': exp.location,
            'start_date': exp.start_date,
            'end_date': exp.end_date,
            'responsibilities': []
        }
        
        for resp in exp.responsibilities:
            exp_data['responsibilities'].append({
                'id': resp.id,
                'description': resp.description,
                'order': resp.order
            })
        
        data['experience'].append(exp_data)
    
    # Projects
    data['projects'] = []
    for proj in cv.projects:
        proj_data = {
            'id': proj.id,
            'title': proj.title,
            'description': proj.description,
            'github_link': proj.github_link,
            'live_link': proj.live_link,
            'start_date': proj.start_date,
            'end_date': proj.end_date,
            'responsibilities': []
        }
        
        for resp in proj.responsibilities:
            proj_data['responsibilities'].append({
                'id': resp.id,
                'description': resp.description,
                'order': resp.order
            })
        
        data['projects'].append(proj_data)
    
    # Languages
    data['languages'] = []
    for cv_lang in cv.cv_languages:
        data['languages'].append({
            'id': cv_lang.id,
            'name': cv_lang.language_item.name,
            'level': cv_lang.level
        })
    
    # Technologies
    data['technologies'] = []
    for cv_tech in cv.cv_technologies:
        data['technologies'].append({
            'id': cv_tech.id,
            'name': cv_tech.technology_item.name,
            'category': cv_tech.technology_item.category,
            'level': cv_tech.level
        })
    
    # Certifications
    data['certifications'] = []
    for cert in cv.certifications:
        data['certifications'].append({
            'id': cert.id,
            'name': cert.name,
            'issuer': cert.issuer,
            'date': cert.date,
            'url': cert.url,
            'description': cert.description
        })
    
    # Interests
    data['interests'] = []
    for interest in cv.interests:
        data['interests'].append({
            'id': interest.id,
            'name': interest.name,
            'description': interest.description
        })
    
    # References
    data['references'] = []
    for ref in cv.references:
        data['references'].append({
            'id': ref.id,
            'name': ref.name,
            'position': ref.position,
            'company': ref.company,
            'email': ref.email,
            'phone': ref.phone,
            'relationship': ref.relationship
        })
    
    # Achievements
    data['achievements'] = []
    for achievement in cv.achievements:
        data['achievements'].append({
            'id': achievement.id,
            'title': achievement.title,
            'description': achievement.description,
            'date': achievement.date
        })
    
    # Publications
    data['publications'] = []
    for pub in cv.publications:
        data['publications'].append({
            'id': pub.id,
            'title': pub.title,
            'publisher': pub.publisher,
            'authors': pub.authors,
            'publication_date': pub.publication_date,
            'url': pub.url,
            'description': pub.description
        })
    
    # Custom Fields
    data['custom_fields'] = []
    for custom in cv.custom_fields:
        data['custom_fields'].append({
            'id': custom.id,
            'field_name': custom.field_name,
            'field_value': custom.field_value,
            'field_type': custom.field_type,
            'order': custom.order
        })
    
    # Update the CV data
    cv.data = data
    db.session.commit()
    return True

# ------------------- Personal Info Functions -------------------

def create_personal_info(cv_id, name, email, phone=None, linkedin=None, github=None, 
                         location=None, image=None, website=None):
    """Create or update personal info for a CV"""
    # Check if personal info already exists
    personal_info = PersonalInfo.query.filter_by(cv_id=cv_id).first()
    
    if personal_info:
        # Update existing personal info
        personal_info.name = name
        personal_info.email = email
        personal_info.phone = phone
        personal_info.linkedin = linkedin
        personal_info.github = github
        personal_info.location = location
        personal_info.image = image
        personal_info.website = website
    else:
        # Create new personal info
        personal_info = PersonalInfo(
            cv_id=cv_id,
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
            location=location,
            image=image,
            website=website
        )
        db.session.add(personal_info)
    
    db.session.commit()
    update_cv_json_data(cv_id)
    return personal_info

def get_personal_info(cv_id):
    """Get personal info for a CV"""
    return PersonalInfo.query.filter_by(cv_id=cv_id).first()

# ------------------- Objective Functions -------------------

def create_objective(cv_id, content, job_title=None):
    """Create a new objective"""
    objective = Objective(
        cv_id=cv_id,
        content=content,
        job_title=job_title
    )
    db.session.add(objective)
    db.session.commit()
    update_cv_json_data(cv_id)
    return objective

def get_objective(objective_id):
    """Get objective by ID"""
    return Objective.query.get(objective_id)

def get_cv_objectives(cv_id):
    """Get all objectives for a CV"""
    return Objective.query.filter_by(cv_id=cv_id).all()

def update_objective(objective_id, content=None, job_title=None):
    """Update an objective"""
    objective = get_objective(objective_id)
    if not objective:
        return None
    
    if content:
        objective.content = content
    if job_title is not None:
        objective.job_title = job_title
    
    db.session.commit()
    update_cv_json_data(objective.cv_id)
    return objective

def delete_objective(objective_id):
    """Delete an objective"""
    objective = get_objective(objective_id)
    if not objective:
        return False
    
    cv_id = objective.cv_id
    db.session.delete(objective)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Education Functions -------------------

def create_education(cv_id, degree, university, start_date=None, end_date=None, 
                     gpa=None, certificate=None, location=None):
    """Create a new education entry"""
    education = Education(
        cv_id=cv_id,
        degree=degree,
        university=university,
        start_date=start_date,
        end_date=end_date,
        gpa=gpa,
        certificate=certificate,
        location=location
    )
    db.session.add(education)
    db.session.commit()
    update_cv_json_data(cv_id)
    return education

def get_education(education_id):
    """Get education by ID"""
    return Education.query.get(education_id)

def get_cv_educations(cv_id):
    """Get all education entries for a CV"""
    return Education.query.filter_by(cv_id=cv_id).all()

def update_education(education_id, degree=None, university=None, start_date=None, 
                     end_date=None, gpa=None, certificate=None, location=None):
    """Update an education entry"""
    education = get_education(education_id)
    if not education:
        return None
    
    if degree:
        education.degree = degree
    if university:
        education.university = university
    if start_date is not None:
        education.start_date = start_date
    if end_date is not None:
        education.end_date = end_date
    if gpa is not None:
        education.gpa = gpa
    if certificate is not None:
        education.certificate = certificate
    if location is not None:
        education.location = location
    
    db.session.commit()
    update_cv_json_data(education.cv_id)
    return education

def delete_education(education_id):
    """Delete an education entry"""
    education = get_education(education_id)
    if not education:
        return False
    
    cv_id = education.cv_id
    db.session.delete(education)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

def add_education_coursework(education_id, course, order=0):
    """Add coursework to education"""
    coursework = EducationCoursework(
        education_id=education_id,
        course=course,
        order=order
    )
    db.session.add(coursework)
    
    # Get cv_id for JSON update
    education = get_education(education_id)
    cv_id = education.cv_id if education else None
    
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return coursework

def update_education_coursework(coursework_id, course=None, order=None):
    """Update education coursework"""
    coursework = EducationCoursework.query.get(coursework_id)
    if not coursework:
        return None
    
    if course:
        coursework.course = course
    if order is not None:
        coursework.order = order
    
    # Get cv_id for JSON update
    education = get_education(coursework.education_id)
    cv_id = education.cv_id if education else None
    
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return coursework

def delete_education_coursework(coursework_id):
    """Delete education coursework"""
    coursework = EducationCoursework.query.get(coursework_id)
    if not coursework:
        return False
    
    # Get cv_id for JSON update
    education = get_education(coursework.education_id)
    cv_id = education.cv_id if education else None
    
    db.session.delete(coursework)
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return True

# ------------------- Experience Functions -------------------

def create_experience(cv_id, role, company, location=None, start_date=None, end_date=None):
    """Create a new experience entry"""
    experience = Experience(
        cv_id=cv_id,
        role=role,
        company=company,
        location=location,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(experience)
    db.session.commit()
    update_cv_json_data(cv_id)
    return experience

def get_experience(experience_id):
    """Get experience by ID"""
    return Experience.query.get(experience_id)

def get_cv_experiences(cv_id):
    """Get all experience entries for a CV"""
    return Experience.query.filter_by(cv_id=cv_id).all()

def update_experience(experience_id, role=None, company=None, location=None, 
                      start_date=None, end_date=None):
    """Update an experience entry"""
    experience = get_experience(experience_id)
    if not experience:
        return None
    
    if role:
        experience.role = role
    if company:
        experience.company = company
    if location is not None:
        experience.location = location
    if start_date is not None:
        experience.start_date = start_date
    if end_date is not None:
        experience.end_date = end_date
    
    db.session.commit()
    update_cv_json_data(experience.cv_id)
    return experience

def delete_experience(experience_id):
    """Delete an experience entry"""
    experience = get_experience(experience_id)
    if not experience:
        return False
    
    cv_id = experience.cv_id
    db.session.delete(experience)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

def add_experience_responsibility(experience_id, description, order=0):
    """Add responsibility to experience"""
    responsibility = ExperienceResponsibility(
        experience_id=experience_id,
        description=description,
        order=order
    )
    db.session.add(responsibility)
    
    # Get cv_id for JSON update
    experience = get_experience(experience_id)
    cv_id = experience.cv_id if experience else None
    
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return responsibility

def update_experience_responsibility(responsibility_id, description=None, order=None):
    """Update experience responsibility"""
    responsibility = ExperienceResponsibility.query.get(responsibility_id)
    if not responsibility:
        return None
    
    if description:
        responsibility.description = description
    if order is not None:
        responsibility.order = order
    
    # Get cv_id for JSON update
    experience = get_experience(responsibility.experience_id)
    cv_id = experience.cv_id if experience else None
    
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return responsibility

def delete_experience_responsibility(responsibility_id):
    """Delete experience responsibility"""
    responsibility = ExperienceResponsibility.query.get(responsibility_id)
    if not responsibility:
        return False
    
    # Get cv_id for JSON update
    experience = get_experience(responsibility.experience_id)
    cv_id = experience.cv_id if experience else None
    
    db.session.delete(responsibility)
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return True

# ------------------- Project Functions -------------------

def create_project(cv_id, title, description=None, github_link=None, live_link=None,
                  start_date=None, end_date=None):
    """Create a new project"""
    project = Project(
        cv_id=cv_id,
        title=title,
        description=description,
        github_link=github_link,
        live_link=live_link,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(project)
    db.session.commit()
    update_cv_json_data(cv_id)
    return project

def get_project(project_id):
    """Get project by ID"""
    return Project.query.get(project_id)

def get_cv_projects(cv_id):
    """Get all projects for a CV"""
    return Project.query.filter_by(cv_id=cv_id).all()

def update_project(project_id, title=None, description=None, github_link=None, 
                  live_link=None, start_date=None, end_date=None):
    """Update a project"""
    project = get_project(project_id)
    if not project:
        return None
    
    if title:
        project.title = title
    if description is not None:
        project.description = description
    if github_link is not None:
        project.github_link = github_link
    if live_link is not None:
        project.live_link = live_link
    if start_date is not None:
        project.start_date = start_date
    if end_date is not None:
        project.end_date = end_date
    
    db.session.commit()
    update_cv_json_data(project.cv_id)
    return project

def delete_project(project_id):
    """Delete a project"""
    project = get_project(project_id)
    if not project:
        return False
    
    cv_id = project.cv_id
    db.session.delete(project)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

def add_project_responsibility(project_id, description, order=0):
    """Add responsibility to project"""
    responsibility = ProjectResponsibility(
        project_id=project_id,
        description=description,
        order=order
    )
    db.session.add(responsibility)
    
    # Get cv_id for JSON update
    project = get_project(project_id)
    cv_id = project.cv_id if project else None
    
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return responsibility

def update_project_responsibility(responsibility_id, description=None, order=None):
    """Update project responsibility"""
    responsibility = ProjectResponsibility.query.get(responsibility_id)
    if not responsibility:
        return None
    
    if description:
        responsibility.description = description
    if order is not None:
        responsibility.order = order
    
    # Get cv_id for JSON update
    project = get_project(responsibility.project_id)
    cv_id = project.cv_id if project else None
    
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return responsibility

def delete_project_responsibility(responsibility_id):
    """Delete project responsibility"""
    responsibility = ProjectResponsibility.query.get(responsibility_id)
    if not responsibility:
        return False
    
    # Get cv_id for JSON update
    project = get_project(responsibility.project_id)
    cv_id = project.cv_id if project else None
    
    db.session.delete(responsibility)
    db.session.commit()
    if cv_id:
        update_cv_json_data(cv_id)
    return True

# ------------------- Language Functions -------------------

def get_all_languages():
    """Get all available languages"""
    return Language.query.order_by(Language.name).all()

def get_language_by_name(name):
    """Get language by name"""
    return Language.query.filter_by(name=name).first()

def search_languages(search_term , limit=20 ):
    """Search languages by name"""
    return Language.query.filter(
            Language.name.ilike(f'%{search_term}%'),
        ).limit(limit).all()

def create_language(name):
    """Create a new language"""
    language = Language(name=name)
    try:
        db.session.add(language)
        db.session.commit()
        return language
    except IntegrityError:
        db.session.rollback()
        return get_language_by_name(name)

def add_language_to_cv(cv_id, language_id, level=None):
    """Add language to CV"""
    # Check if already exists
    existing = CVLanguage.query.filter_by(cv_id=cv_id, language_id=language_id).first()
    if existing:
        if level is not None:
            existing.level = level
            db.session.commit()
        update_cv_json_data(cv_id)
        return existing
    
    cv_language = CVLanguage(
        cv_id=cv_id,
        language_id=language_id,
        level=level
    )
    db.session.add(cv_language)
    db.session.commit()
    update_cv_json_data(cv_id)
    return cv_language

def get_cv_languages(cv_id):
    """Get all languages for a CV"""
    return CVLanguage.query.filter_by(cv_id=cv_id).all()

def update_cv_language(cv_language_id, level=None):
    """Update CV language level"""
    cv_language = CVLanguage.query.get(cv_language_id)
    if not cv_language:
        return None
    
    if level is not None:
        cv_language.level = level
    
    db.session.commit()
    update_cv_json_data(cv_language.cv_id)
    return cv_language

def remove_language_from_cv(cv_language_id):
    """Remove language from CV"""
    cv_language = CVLanguage.query.get(cv_language_id)
    if not cv_language:
        return False
    
    cv_id = cv_language.cv_id
    db.session.delete(cv_language)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Technology Functions -------------------

def get_all_technologies(limit=None):
    """Get all available technologies"""
    return Technology.query.order_by(Technology.name).limit(limit).all()

def get_technologies_by_category(category):
    """Get technologies by category"""
    return Technology.query.filter_by(category=category).order_by(Technology.name).all()

def get_technology_by_name(name):
    """Get technology by name"""
    return Technology.query.filter_by(name=name).first()

def search_technologies(search_term , limit=20 ):
    """Search technologies by name"""
    return Technology.query.filter(
            Technology.name.ilike(f'%{search_term}%'),
        ).limit(limit).all()

def create_technology(name, category=None):
    """Create a new technology"""
    tech = Technology(name=name, category=category)
    try:
        db.session.add(tech)
        db.session.commit()
        return tech
    except IntegrityError:
        db.session.rollback()
        return get_technology_by_name(name)

def add_technology_to_cv(cv_id, technology_id, level=None):
    """Add technology to CV"""
    # Check if already exists
    existing = CVTechnology.query.filter_by(cv_id=cv_id, technology_id=technology_id).first()
    if existing:
        if level is not None:
            existing.level = level
            db.session.commit()
        update_cv_json_data(cv_id)
        return existing
    
    cv_technology = CVTechnology(
        cv_id=cv_id,
        technology_id=technology_id,
        level=level
    )
    db.session.add(cv_technology)
    db.session.commit()
    update_cv_json_data(cv_id)
    return cv_technology

def get_cv_technologies(cv_id):
    """Get all technologies for a CV"""
    return CVTechnology.query.filter_by(cv_id=cv_id).all()

def update_cv_technology(cv_technology_id, level=None):
    """Update CV technology level"""
    cv_technology = CVTechnology.query.get(cv_technology_id)
    if not cv_technology:
        return None
    
    if level is not None:
        cv_technology.level = level
    
    db.session.commit()
    update_cv_json_data(cv_technology.cv_id)
    return cv_technology

def remove_technology_from_cv(cv_technology_id):
    """Remove technology from CV"""
    cv_technology = CVTechnology.query.get(cv_technology_id)
    if not cv_technology:
        return False
    
    cv_id = cv_technology.cv_id
    db.session.delete(cv_technology)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Certificate Functions -------------------

def create_certification(cv_id, name, issuer=None, date=None, url=None, description=None):
    """Create a new certification"""
    cert = Certification(
        cv_id=cv_id,
        name=name,
        issuer=issuer,
        date=date,
        url=url,
        description=description
    )
    db.session.add(cert)
    db.session.commit()
    update_cv_json_data(cv_id)
    return cert

def get_certification(cert_id):
    """Get certification by ID"""
    return Certification.query.get(cert_id)

def get_cv_certifications(cv_id):
    """Get all certifications for a CV"""
    return Certification.query.filter_by(cv_id=cv_id).all()

def update_certification(cert_id, name=None, issuer=None, date=None, url=None, description=None):
    """Update a certification"""
    cert = get_certification(cert_id)
    if not cert:
        return None
    
    if name:
        cert.name = name
    if issuer is not None:
        cert.issuer = issuer
    if date is not None:
        cert.date = date
    if url is not None:
        cert.url = url
    if description is not None:
        cert.description = description
    
    db.session.commit()
    update_cv_json_data(cert.cv_id)
    return cert

def delete_certification(cert_id):
    """Delete a certification"""
    cert = get_certification(cert_id)
    if not cert:
        return False
    
    cv_id = cert.cv_id
    db.session.delete(cert)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Interest Functions -------------------

def create_interest(cv_id, name, description=None):
    """Create a new interest"""
    interest = Interest(
        cv_id=cv_id,
        name=name,
        description=description
    )
    db.session.add(interest)
    db.session.commit()
    update_cv_json_data(cv_id)
    return interest

def get_interest(interest_id):
    """Get interest by ID"""
    return Interest.query.get(interest_id)

def get_cv_interests(cv_id):
    """Get all interests for a CV"""
    return Interest.query.filter_by(cv_id=cv_id).all()

def update_interest(interest_id, name=None, description=None):
    """Update an interest"""
    interest = get_interest(interest_id)
    if not interest:
        return None
    
    if name:
        interest.name = name
    if description is not None:
        interest.description = description
    
    db.session.commit()
    update_cv_json_data(interest.cv_id)
    return interest

def delete_interest(interest_id):
    """Delete an interest"""
    interest = get_interest(interest_id)
    if not interest:
        return False
    
    cv_id = interest.cv_id
    db.session.delete(interest)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Reference Functions -------------------

def create_reference(cv_id, name, position=None, company=None, email=None, 
                    phone=None, relationship=None):
    """Create a new reference"""
    reference = Reference(
        cv_id=cv_id,
        name=name,
        position=position,
        company=company,
        email=email,
        phone=phone,
        relationship=relationship
    )
    db.session.add(reference)
    db.session.commit()
    update_cv_json_data(cv_id)
    return reference

def get_reference(reference_id):
    """Get reference by ID"""
    return Reference.query.get(reference_id)

def get_cv_references(cv_id):
    """Get all references for a CV"""
    return Reference.query.filter_by(cv_id=cv_id).all()

def update_reference(reference_id, name=None, position=None, company=None, 
                    email=None, phone=None, relationship=None):
    """Update a reference"""
    reference = get_reference(reference_id)
    if not reference:
        return None
    
    if name:
        reference.name = name
    if position is not None:
        reference.position = position
    if company is not None:
        reference.company = company
    if email is not None:
        reference.email = email
    if phone is not None:
        reference.phone = phone
    if relationship is not None:
        reference.relationship = relationship
    
    db.session.commit()
    update_cv_json_data(reference.cv_id)
    return reference

def delete_reference(reference_id):
    """Delete a reference"""
    reference = get_reference(reference_id)
    if not reference:
        return False
    
    cv_id = reference.cv_id
    db.session.delete(reference)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Achievement Functions -------------------

def create_achievement(cv_id, title, description=None, date=None):
    """Create a new achievement"""
    achievement = Achievement(
        cv_id=cv_id,
        title=title,
        description=description,
        date=date
    )
    db.session.add(achievement)
    db.session.commit()
    update_cv_json_data(cv_id)
    return achievement

def get_achievement(achievement_id):
    """Get achievement by ID"""
    return Achievement.query.get(achievement_id)

def get_cv_achievements(cv_id):
    """Get all achievements for a CV"""
    return Achievement.query.filter_by(cv_id=cv_id).all()

def update_achievement(achievement_id, title=None, description=None, date=None):
    """Update an achievement"""
    achievement = get_achievement(achievement_id)
    if not achievement:
        return None
    
    if title:
        achievement.title = title
    if description is not None:
        achievement.description = description
    if date is not None:
        achievement.date = date
    
    db.session.commit()
    update_cv_json_data(achievement.cv_id)
    return achievement

def delete_achievement(achievement_id):
    """Delete an achievement"""
    achievement = get_achievement(achievement_id)
    if not achievement:
        return False
    
    cv_id = achievement.cv_id
    db.session.delete(achievement)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Publication Functions -------------------

def create_publication(cv_id, title, publisher=None, authors=None, publication_date=None,
                      url=None, description=None):
    """Create a new publication"""
    publication = Publication(
        cv_id=cv_id,
        title=title,
        publisher=publisher,
        authors=authors,
        publication_date=publication_date,
        url=url,
        description=description
    )
    db.session.add(publication)
    db.session.commit()
    update_cv_json_data(cv_id)
    return publication

def get_publication(publication_id):
    """Get publication by ID"""
    return Publication.query.get(publication_id)

def get_cv_publications(cv_id):
    """Get all publications for a CV"""
    return Publication.query.filter_by(cv_id=cv_id).all()

def update_publication(publication_id, title=None, publisher=None, authors=None, 
                      publication_date=None, url=None, description=None):
    """Update a publication"""
    publication = get_publication(publication_id)
    if not publication:
        return None
    
    if title:
        publication.title = title
    if publisher is not None:
        publication.publisher = publisher
    if authors is not None:
        publication.authors = authors
    if publication_date is not None:
        publication.publication_date = publication_date
    if url is not None:
        publication.url = url
    if description is not None:
        publication.description = description
    
    db.session.commit()
    update_cv_json_data(publication.cv_id)
    return publication

def delete_publication(publication_id):
    """Delete a publication"""
    publication = get_publication(publication_id)
    if not publication:
        return False
    
    cv_id = publication.cv_id
    db.session.delete(publication)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Custom Field Functions -------------------

def create_custom_field(cv_id, field_name, field_value, field_type=None, order=0):
    """Create a new custom field"""
    custom_field = CustomField(
        cv_id=cv_id,
        field_name=field_name,
        field_value=field_value,
        field_type=field_type,
        order=order
    )
    db.session.add(custom_field)
    db.session.commit()
    update_cv_json_data(cv_id)
    return custom_field

def get_custom_field(custom_field_id):
    """Get custom field by ID"""
    return CustomField.query.get(custom_field_id)

def get_cv_custom_fields(cv_id):
    """Get all custom fields for a CV"""
    return CustomField.query.filter_by(cv_id=cv_id).order_by(CustomField.order).all()

def update_custom_field(custom_field_id, field_name=None, field_value=None, 
                       field_type=None, order=None):
    """Update a custom field"""
    custom_field = get_custom_field(custom_field_id)
    if not custom_field:
        return None
    
    if field_name:
        custom_field.field_name = field_name
    if field_value is not None:
        custom_field.field_value = field_value
    if field_type is not None:
        custom_field.field_type = field_type
    if order is not None:
        custom_field.order = order
    
    db.session.commit()
    update_cv_json_data(custom_field.cv_id)
    return custom_field

def delete_custom_field(custom_field_id):
    """Delete a custom field"""
    custom_field = get_custom_field(custom_field_id)
    if not custom_field:
        return False
    
    cv_id = custom_field.cv_id
    db.session.delete(custom_field)
    db.session.commit()
    update_cv_json_data(cv_id)
    return True

# ------------------- Template Functions -------------------

def create_template(name, data, preview_image=None, description=None, 
                   is_require_image=False, is_require_personal_info=False,
                   is_require_objective=False, is_require_educations=False,
                   is_require_experiences=False, is_require_projects=False,
                   is_require_languages=False, is_require_technologies=False,
                   is_require_achievements=False, is_require_references=False,
                   is_require_interests=False, is_require_certifications=False,
                   is_require_publications=False, is_active=True):
    """Create a new template"""
    template = Template(
        name=name,
        data=data,
        preview_image=preview_image,
        description=description,
        is_require_image=is_require_image,
        is_require_personal_info=is_require_personal_info,
        is_require_objective=is_require_objective,
        is_require_educations=is_require_educations,
        is_require_experiences=is_require_experiences,
        is_require_projects=is_require_projects,
        is_require_languages=is_require_languages,
        is_require_technologies=is_require_technologies,
        is_require_achievements=is_require_achievements,
        is_require_references=is_require_references,
        is_require_interests=is_require_interests,
        is_require_certifications=is_require_certifications,
        is_require_publications=is_require_publications,
        is_active=is_active
    )
    db.session.add(template)
    db.session.commit()
    return template

def get_template(template_id):
    """Get template by ID"""
    return Template.query.get(template_id)

def get_all_templates(active_only=True):
    """Get all templates"""
    query = Template.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(Template.name).all()

def update_template(template_id, name=None, data=None, preview_image=None, 
                   description=None, is_active=None, **requirements):
    """Update a template"""
    template = get_template(template_id)
    if not template:
        return None
    
    if name:
        template.name = name
    if data:
        template.data = data
    if preview_image is not None:
        template.preview_image = preview_image
    if description is not None:
        template.description = description
    if is_active is not None:
        template.is_active = is_active
    
    # Update requirements if provided
    for key, value in requirements.items():
        if hasattr(template, key) and value is not None:
            setattr(template, key, value)
    
    db.session.commit()
    return template

def delete_template(template_id):
    """Delete a template"""
    template = get_template(template_id)
    if not template:
        return False
    
    # Check if template is used by any CV
    if CVData.query.filter_by(template_id=template_id).first():
        # Don't actually delete, just mark as inactive
        template.is_active = False
        db.session.commit()
        return True
    
    db.session.delete(template)
    db.session.commit()
    return True

# ------------------- Component Library Functions -------------------

def add_to_component_library(user_id, component_type, component_id, name):
    """Add a component to the user's library"""
    # Check if component already exists in library
    existing = ComponentLibrary.query.filter_by(
        user_id=user_id, 
        component_type=component_type, 
        component_id=component_id
    ).first()
    
    if existing:
        existing.name = name
        db.session.commit()
        return existing
    
    library_item = ComponentLibrary(
        user_id=user_id,
        component_type=component_type,
        component_id=component_id,
        name=name
    )
    db.session.add(library_item)
    db.session.commit()
    return library_item

def get_user_component_library(user_id, component_type=None):
    """Get all components from user's library, optionally filtered by type"""
    query = ComponentLibrary.query.filter_by(user_id=user_id)
    if component_type:
        query = query.filter_by(component_type=component_type)
    return query.order_by(ComponentLibrary.component_type, ComponentLibrary.name).all()

def remove_from_component_library(library_item_id):
    """Remove a component from the library"""
    library_item = ComponentLibrary.query.get(library_item_id)
    if not library_item:
        return False
    
    db.session.delete(library_item)
    db.session.commit()
    return True

def use_library_component(cv_id, library_item_id):
    """Copy a component from the library to a CV"""
    library_item = ComponentLibrary.query.get(library_item_id)
    if not library_item:
        return None
    
    component_type = library_item.component_type
    component_id = library_item.component_id
    
    if component_type == 'education':
        return _copy_education(component_id, cv_id)
    elif component_type == 'experience':
        return _copy_experience(component_id, cv_id)
    elif component_type == 'project':
        return _copy_project(component_id, cv_id)
    elif component_type == 'objective':
        return _copy_objective(component_id, cv_id)
    elif component_type == 'certification':
        return _copy_certification(component_id, cv_id)
    elif component_type == 'achievement':
        return _copy_achievement(component_id, cv_id)
    elif component_type == 'publication':
        return _copy_publication(component_id, cv_id)
    elif component_type == 'reference':
        return _copy_reference(component_id, cv_id)
    
    return None

# ------------------- Helper Functions for Component Library -------------------

def _copy_education(source_id, target_cv_id):
    """Copy education from one CV to another"""
    source = get_education(source_id)
    if not source:
        return None
    
    new_edu = create_education(
        cv_id=target_cv_id,
        degree=source.degree,
        university=source.university,
        start_date=source.start_date,
        end_date=source.end_date,
        gpa=source.gpa,
        certificate=source.certificate,
        location=source.location
    )
    
    # Copy coursework
    for course in source.coursework:
        add_education_coursework(
            education_id=new_edu.id,
            course=course.course,
            order=course.order
        )
    
    return new_edu

def _copy_experience(source_id, target_cv_id):
    """Copy experience from one CV to another"""
    source = get_experience(source_id)
    if not source:
        return None
    
    new_exp = create_experience(
        cv_id=target_cv_id,
        role=source.role,
        company=source.company,
        location=source.location,
        start_date=source.start_date,
        end_date=source.end_date
    )
    
    # Copy responsibilities
    for resp in source.responsibilities:
        add_experience_responsibility(
            experience_id=new_exp.id,
            description=resp.description,
            order=resp.order
        )
    
    return new_exp

def _copy_project(source_id, target_cv_id):
    """Copy project from one CV to another"""
    source = get_project(source_id)
    if not source:
        return None
    
    new_proj = create_project(
        cv_id=target_cv_id,
        title=source.title,
        description=source.description,
        github_link=source.github_link,
        live_link=source.live_link,
        start_date=source.start_date,
        end_date=source.end_date
    )
    
    # Copy responsibilities
    for resp in source.responsibilities:
        add_project_responsibility(
            project_id=new_proj.id,
            description=resp.description,
            order=resp.order
        )
    
    return new_proj

def _copy_objective(source_id, target_cv_id):
    """Copy objective from one CV to another"""
    source = get_objective(source_id)
    if not source:
        return None
    
    return create_objective(
        cv_id=target_cv_id,
        content=source.content,
        job_title=source.job_title
    )

def _copy_certification(source_id, target_cv_id):
    """Copy certification from one CV to another"""
    source = get_certification(source_id)
    if not source:
        return None
    
    return create_certification(
        cv_id=target_cv_id,
        name=source.name,
        issuer=source.issuer,
        date=source.date,
        url=source.url,
        description=source.description
    )

def _copy_achievement(source_id, target_cv_id):
    """Copy achievement from one CV to another"""
    source = get_achievement(source_id)
    if not source:
        return None
    
    return create_achievement(
        cv_id=target_cv_id,
        title=source.title,
        description=source.description,
        date=source.date
    )

def _copy_publication(source_id, target_cv_id):
    """Copy publication from one CV to another"""
    source = get_publication(source_id)
    if not source:
        return None
    
    return create_publication(
        cv_id=target_cv_id,
        title=source.title,
        publisher=source.publisher,
        authors=source.authors,
        publication_date=source.publication_date,
        url=source.url,
        description=source.description
    )

def _copy_reference(source_id, target_cv_id):
    """Copy reference from one CV to another"""
    source = get_reference(source_id)
    if not source:
        return None
    
    return create_reference(
        cv_id=target_cv_id,
        name=source.name,
        position=source.position,
        company=source.company,
        email=source.email,
        phone=source.phone,
        relationship=source.relationship
    )

# ------------------- Contact Message Functions -------------------

def create_contact_message(name, email, message, user_id=None):
    """Create a new contact message"""
    contact = ContactMessage(
        name=name,
        email=email,
        message=message,
        user_id=user_id
    )
    db.session.add(contact)
    db.session.commit()
    return contact

def get_contact_message(message_id):
    """Get contact message by ID"""
    return ContactMessage.query.get(message_id)

def get_all_contact_messages(user_id=None):
    """Get all contact messages, optionally filtered by user"""
    query = ContactMessage.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    return query.order_by(ContactMessage.created_at.desc()).all()

def delete_contact_message(message_id):
    """Delete a contact message"""
    message = get_contact_message(message_id)
    if not message:
        return False
    
    db.session.delete(message)
    db.session.commit()
    return True