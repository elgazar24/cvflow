from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import login_manager
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password, 
            method='pbkdf2:sha256',
            salt_length=8
        )
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_password=False):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'password_hash': self.password_hash if include_password else None
        }


class CVData(db.Model):
    """Main CV model that stores complete CV information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    cv_pdf_name = db.Column(db.String(255), nullable=True)
    cv_json_name = db.Column(db.String(255), nullable=True)
    cv_latex_name = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Store complete CV data as JSON for easy rendering
    data = db.Column(db.JSON , nullable=False)
    
    # Define relationships
    user = db.relationship('User', backref=db.backref('cvs', lazy=True))
    template = db.relationship('Template', backref=db.backref('cvs', lazy=True))
    
    # Relationships to CV components
    personal_info = db.relationship('PersonalInfo', backref='cv', lazy=True, uselist=False)
    objectives = db.relationship('Objective', backref='cv', lazy=True)
    educations = db.relationship('Education', backref='cv', lazy=True)
    experiences = db.relationship('Experience', backref='cv', lazy=True)
    projects = db.relationship('Project', backref='cv', lazy=True)
    certifications = db.relationship('Certification', backref='cv', lazy=True)
    interests = db.relationship('Interest', backref='cv', lazy=True)
    references = db.relationship('Reference', backref='cv', lazy=True)
    achievements = db.relationship('Achievement', backref='cv', lazy=True)
    publications = db.relationship('Publication', backref='cv', lazy=True)
    custom_fields = db.relationship('CustomField', backref='cv', lazy=True)
    
    # Many-to-many relationships
    cv_languages = db.relationship('CVLanguage', backref='cv', lazy=True)
    cv_technologies = db.relationship('CVTechnology', backref='cv', lazy=True)
    
    def update_json_data(self):
        """Update the JSON data field with current component data"""
        # Logic to aggregate all component data into the data JSON field
        pass

    def to_dict(self, include_relationships=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'template_id': self.template_id,
            'cv_pdf_name': self.cv_pdf_name,
            'cv_json_name': self.cv_json_name,
            'cv_latex_name': self.cv_latex_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'data': self.data
        }
        
        if include_relationships:
            data.update({
                'personal_info': self.personal_info.to_dict() if self.personal_info else None,
                'objectives': [obj.to_dict() for obj in self.objectives],
                'educations': [edu.to_dict() for edu in self.educations],
                'experiences': [exp.to_dict() for exp in self.experiences],
                'projects': [proj.to_dict() for proj in self.projects],
                'certifications': [cert.to_dict() for cert in self.certifications],
                'interests': [interest.to_dict() for interest in self.interests],
                'references': [ref.to_dict() for ref in self.references],
                'achievements': [ach.to_dict() for ach in self.achievements],
                'publications': [pub.to_dict() for pub in self.publications],
                'custom_fields': [field.to_dict() for field in self.custom_fields],
                'languages': [lang.to_dict() for lang in self.cv_languages],
                'technologies': [tech.to_dict() for tech in self.cv_technologies]
            })
        
        return data


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    user = db.relationship('User', backref=db.backref('messages', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class Technology(db.Model):
    """Master table of available technologies"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=True)  # e.g., Programming Languages, Frameworks, etc.
    
    # Relationship to CVTechnology
    cv_technologies = db.relationship('CVTechnology', backref='technology_item', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category
        }


class CVTechnology(db.Model):
    """Association table between CVs and technologies"""
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    technology_id = db.Column(db.Integer, db.ForeignKey('technology.id'), nullable=False)
    level = db.Column(db.String(100), nullable=True)  # e.g., Beginner, Intermediate, Expert
    
    __table_args__ = (db.UniqueConstraint('cv_id', 'technology_id', name='uix_cv_technology'),)

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'technology_id': self.technology_id,
            'level': self.level,
        }



class Language(db.Model):
    """Master table of available languages"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Relationship to CVLanguage
    cv_languages = db.relationship('CVLanguage', backref='language_item', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }



class CVLanguage(db.Model):
    """Association table between CVs and languages"""
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)
    level = db.Column(db.String(100), nullable=True)  # e.g., Native, Fluent, Intermediate
    
    __table_args__ = (db.UniqueConstraint('cv_id', 'language_id', name='uix_cv_language'),)

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'language_id': self.language_id,
            'level': self.level,
            'language': self.language_item.to_dict() if self.language_item else None
        }



class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data = db.Column(db.JSON, nullable=False)  # Template configuration
    preview_image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_require_image = db.Column(db.Boolean, default=False)
    is_require_personal_info = db.Column(db.Boolean, default=False)
    is_require_objective = db.Column(db.Boolean, default=False)
    is_require_educations = db.Column(db.Boolean, default=False)
    is_require_experiences = db.Column(db.Boolean, default=False)
    is_require_projects = db.Column(db.Boolean, default=False)
    is_require_languages = db.Column(db.Boolean, default=False)
    is_require_technologies = db.Column(db.Boolean, default=False)
    is_require_achievements = db.Column(db.Boolean, default=False)
    is_require_references = db.Column(db.Boolean, default=False)
    is_require_interests = db.Column(db.Boolean, default=False)
    is_require_certifications = db.Column(db.Boolean, default=False)
    is_require_publications = db.Column(db.Boolean, default=False)
    is_require_custom_fields = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'data': self.data,
            'preview_image': self.preview_image,
            'description': self.description,
            'is_require_image': self.is_require_image,
            'is_require_personal_info': self.is_require_personal_info,
            'is_require_objective': self.is_require_objective,
            'is_require_educations': self.is_require_educations,
            'is_require_experiences': self.is_require_experiences,
            'is_require_projects': self.is_require_projects,
            'is_require_languages': self.is_require_languages,
            'is_require_technologies': self.is_require_technologies,
            'is_require_achievements': self.is_require_achievements,
            'is_require_references': self.is_require_references,
            'is_require_interests': self.is_require_interests,
            'is_require_certifications': self.is_require_certifications,
            'is_require_publications': self.is_require_publications,
            'is_require_custom_fields': self.is_require_custom_fields,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    

class TemplateStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    


class PersonalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    github = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'linkedin': self.linkedin,
            'github': self.github,
            'location': self.location,
            'image': self.image,
            'website': self.website,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    github_link = db.Column(db.String(255), nullable=True)
    live_link = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.String(50), nullable=True)
    end_date = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    responsibilities = db.relationship('ProjectResponsibility', backref='project', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'title': self.title,
            'description': self.description,
            'github_link': self.github_link,
            'live_link': self.live_link,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'responsibilities': [resp.to_dict() for resp in self.responsibilities]
        }


class ProjectResponsibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'description': self.description,
            'order': self.order
        }


class Objective(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    job_title = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'content': self.content,
            'job_title': self.job_title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    degree = db.Column(db.String(200), nullable=False)
    university = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.String(50), nullable=True)
    end_date = db.Column(db.String(50), nullable=True)
    gpa = db.Column(db.String(20), nullable=True)
    certificate = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    coursework = db.relationship('EducationCoursework', backref='education', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'degree': self.degree,
            'university': self.university,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'gpa': self.gpa,
            'certificate': self.certificate,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class EducationCoursework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    education_id = db.Column(db.Integer, db.ForeignKey('education.id'), nullable=False)
    course = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'education_id': self.education_id,
            'course': self.course,
            'order': self.order
        }


class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    start_date = db.Column(db.String(50), nullable=True)
    end_date = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    responsibilities = db.relationship('ExperienceResponsibility', backref='experience', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'role': self.role,
            'company': self.company,
            'location': self.location,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ExperienceResponsibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experience_id = db.Column(db.Integer, db.ForeignKey('experience.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'experience_id': self.experience_id,
            'description': self.description,
            'order': self.order
        }


class Certification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), nullable=True)
    date = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'name': self.name,
            'issuer': self.issuer,
            'date': self.date,
            'url': self.url,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Reference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(200), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    relationship = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'name': self.name,
            'position': self.position,
            'company': self.company,
            'email': self.email,
            'phone': self.phone,
            'relationship': self.relationship,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Publication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publisher = db.Column(db.String(200), nullable=True)
    authors = db.Column(db.String(255), nullable=True)
    publication_date = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'title': self.title,
            'publisher': self.publisher,
            'authors': self.authors,
            'publication_date': self.publication_date,
            'url': self.url,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CustomField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cv_data.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_value = db.Column(db.Text, nullable=False)
    field_type = db.Column(db.String(50), nullable=True)  # text, date, list, etc.
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'cv_id': self.cv_id,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'field_type': self.field_type,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Library for shared CV components
class ComponentLibrary(db.Model):
    """Store reusable CV components that can be shared across multiple CVs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    component_type = db.Column(db.String(50), nullable=False)  # education, experience, project, etc.
    component_id = db.Column(db.Integer, nullable=False)  # ID of the stored component
    name = db.Column(db.String(200), nullable=False)  # Name for easy user selection
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    user = db.relationship('User', backref=db.backref('component_library', lazy=True))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'component_type', 'component_id', name='uix_user_component'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'component_type': self.component_type,
            'component_id': self.component_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }