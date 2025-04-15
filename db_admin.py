
# db_access.py
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import json
from models import User, CVData, ContactMessage  # Import your models

# Use the same connection string as your Flask app
DATABASE_URI = 'postgresql://cvflow_user:me2737050@localhost/cvflow'

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def list_all_users():
    session = get_db_session()
    try:
        users = session.query(User).all()
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Username: {user.username}" )
    finally:
        session.close()

def get_messages():
    session = get_db_session()
    try:
        messages = session.query(ContactMessage).all()
        for message in messages:
            print(f"ID: {message.id}, Name: {message.name}, Email: {message.email}, Message: {message.message}" )
    finally:
        session.close()

def get_user_cv(user_id):
    session = get_db_session()
    try:
        cv_data = session.query(CVData).filter_by(user_id=user_id).first()
        if cv_data:
            print(f"CV Data for User {user_id}:")
            print(json.dumps(cv_data.data, indent=2))
        else:
            print(f"No CV data found for user {user_id}")
    finally:
        session.close()

if __name__ == '__main__':
    print("=== Database Access Program ===")
    print("1. List all users")
    print("2. Get user CV data")   
    print("3. Get messages") 
    while 1 :
        choice = input("Select option: ")
        if choice == "1":
            list_all_users()
        elif choice == "2":
            user_id = input("Enter user ID: ")
            get_user_cv(int(user_id))
        elif choice == "3":
            get_messages()
        else:
            break