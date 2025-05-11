#!/usr/bin/env python3
import os
from app import create_app, db
from models import *  # Import all your models
import db_access

def reset_database():
    app = create_app()
    
    with app.app_context():
        print("⚠️ WARNING: This will DROP ALL TABLES and RECREATE THEM!")
        print("All data will be permanently lost!")
        confirmation = input("Type 'RESET' to confirm: ")
        
        if confirmation != 'RESET':
            print("Operation cancelled")
            return

        try:
            # 1. Drop all tables
            print("Dropping all tables...")
            db.reflect()
            db.drop_all()
            
            # 2. Recreate tables
            print("Creating tables...")
            db.create_all()
            
            print("✅ Database reset complete!")
            
            # Optional: Add initial data
            if input("Add default templates? (y/n): ").lower() == 'y':

                # Add default templates
                db_access.create_template("Default", "This is a default template", "default")
                db_access.create_template("Professional", "This is an Professional template", "Professional")
                db_access.create_template("Simple", "This is a Simple template", "Simple")


                # Add default languages
                db_access.create_language("English")
                db_access.create_language("Spanish")
                db_access.create_language("Arabic")
                db_access.create_language("French")

                # Add default technologies
                db_access.create_technology("Python")
                db_access.create_technology("Java")
                db_access.create_technology("C++")
                db_access.create_technology("C#")
                db_access.create_technology("C")
                db_access.create_technology("HTML")
                db_access.create_technology("CSS")
                db_access.create_technology("JavaScript")
                db_access.create_technology("Dart")
                db_access.create_technology("Flutter")
                db_access.create_technology("React")
                db_access.create_technology("Node.js")
                db_access.create_technology("Express.js")
                db_access.create_technology("MongoDB")
                db_access.create_technology("MySQL")
                db_access.create_technology("PostgreSQL")
                db_access.create_technology("Git")
                db_access.create_technology("Docker")
                db_access.create_technology("Kubernetes")
                db_access.create_technology("AWS")
                db_access.create_technology("GCP")
                db_access.create_technology("Azure")

                print("Added defaults")
                
        except Exception as e:
            print(f"❌ Error resetting database: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    reset_database()