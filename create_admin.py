from app import app, db, User
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

def create_admin():
    with app.app_context():
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        # Check if admin exists
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                name='Administrator',
                email=admin_email,
                phone='0000000000',
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created with email: {admin_email}")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    create_admin()
