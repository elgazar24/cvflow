import streamlit as st
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, CVData, ContactMessage, Skill, Template
from werkzeug.security import generate_password_hash

# Database setup
DATABASE_URI = 'postgresql://cvflow_user:me2737050@localhost/cvflow'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# Utility
def run_session(action):
    session = Session()
    try:
        return action(session)
    finally:
        session.close()

# --- Streamlit GUI ---
st.set_page_config(page_title="CVFlow DB Admin Panel", layout="wide")
st.title("CVFlow DB Admin Panel")

menu = [
    "List Users", "Get Messages", "Get User CV",
    "List Skills", "Add Skill", "Remove Skill",
    "Add User", "Remove User",
    "List Templates", "Add Template", "Delete Template"
]

choice = st.sidebar.selectbox("Choose an action", menu)

# --- Functions ---
def list_users():
    def action(session):
        users = session.query(User).all()
        return "\n".join([f"[{u.id}] {u.username} | {u.email}" for u in users]) or "No users found."
    st.text(run_session(action))

def list_messages():
    def action(session):
        messages = session.query(ContactMessage).all()
        return "\n\n".join([f"[{m.id}] {m.name} <{m.email}>\n{m.message}\n{m.created_at}\n{'-'*40}" for m in messages]) or "No messages."
    st.text(run_session(action))

def list_cv_data():
    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Get CV Data"):
        def action(session):
            cv = session.query(CVData).filter_by(user_id=user_id).first()
            return json.dumps(cv.data, indent=2) if cv else "No CV data found."
        st.code(run_session(action))

def list_skills():
    def action(session):
        skills = session.query(Skill).all()
        return "\n".join([f"{s.id}: {s.name} ({s.category})" for s in skills]) or "No skills."
    st.text(run_session(action))

def add_skill():
    name = st.text_input("Skill Name")
    category = st.text_input("Skill Category")
    if st.button("Add Skill"):
        if name and category:
            def action(session):
                skill = Skill(name=name, category=category)
                session.add(skill)
                session.commit()
                return f"Skill '{name}' added."
            st.success(run_session(action))
        else:
            st.error("Both fields required.")

def remove_skill():
    skill_id = st.number_input("Enter Skill ID", min_value=1, step=1)
    if st.button("Remove Skill"):
        def action(session):
            skill = session.query(Skill).get(skill_id)
            if skill:
                session.delete(skill)
                session.commit()
                return f"Skill ID {skill_id} removed."
            return "Skill not found."
        st.success(run_session(action))

def add_user():
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Add User"):
        if all([username, email, password]):
            def action(session):
                if session.query(User).filter_by(email=email).first():
                    return "User already exists."
                user = User(username=username, email=email)
                user.set_password(password)
                session.add(user)
                session.commit()
                return f"User {username} added."
            st.success(run_session(action))
        else:
            st.error("All fields required.")

def remove_user():
    user_id = st.number_input("Enter User ID", min_value=1, step=1)
    if st.button("Remove User"):
        def action(session):
            user = session.query(User).get(user_id)
            if user:
                session.delete(user)
                session.commit()
                return f"User ID {user_id} removed."
            return "User not found."
        st.success(run_session(action))

def list_templates():
    def action(session):
        templates = session.query(Template).all()
        return "\n\n".join([f"[{t.id}] {t.name}\n{json.dumps(t.data, indent=2)}\n{'-'*30}" for t in templates]) or "No templates."
    st.text(run_session(action))

def add_template():
    name = st.text_input("Template Name")
    raw_json = st.text_area("Template JSON")
    if st.button("Add Template"):
        try:
            data = json.loads(raw_json)
            def action(session):
                template = Template(name=name, data=data)
                session.add(template)
                session.commit()
                return f"Template '{name}' added."
            st.success(run_session(action))
        except json.JSONDecodeError:
            st.error("Invalid JSON")

def delete_template():
    template_id = st.number_input("Enter Template ID", min_value=1, step=1)
    if st.button("Delete Template"):
        def action(session):
            template = session.query(Template).get(template_id)
            if template:
                session.delete(template)
                session.commit()
                return f"Template ID {template_id} deleted."
            return "Template not found."
        st.success(run_session(action))

# --- Run selected feature ---
if choice == "List Users":
    list_users()
elif choice == "Get Messages":
    list_messages()
elif choice == "Get User CV":
    list_cv_data()
elif choice == "List Skills":
    list_skills()
elif choice == "Add Skill":
    add_skill()
elif choice == "Remove Skill":
    remove_skill()
elif choice == "Add User":
    add_user()
elif choice == "Remove User":
    remove_user()
elif choice == "List Templates":
    list_templates()
elif choice == "Add Template":
    add_template()
elif choice == "Delete Template":
    delete_template()
