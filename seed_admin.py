#!/usr/bin/env python3
"""
Script to seed the database with an initial admin user.
Run this after setting up the database.
"""

from app.database import SessionLocal, engine, Base
from app.models import User, UserRole
from app.auth import get_password_hash

def create_admin():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if existing_admin:
            print("Admin user already exists!")
            return

        # Create admin user
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),  # Change this password in production!
            role=UserRole.ADMIN,
            full_name="System Administrator"
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login!")

    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
