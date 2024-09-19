from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
import logging

def init_database():
    app = create_app()
    with app.app_context():
        try:
            # Drop all existing tables
            db.drop_all()
            logging.info("Existing tables dropped.")

            # Create all tables (this will only create the users table)
            db.create_all()
            logging.info("Users table created.")

            # Create admin user
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                accessible_tables='',  # Initially empty, will be populated as tables are created
                permissions='view,edit,update,create',  # Include 'create' permission for creating new tables
                is_admin=True  # Make sure your User model has this field
            )

            db.session.add(admin)
            db.session.commit()
            logging.info("Admin user created.")

            logging.info("Database initialized with users table and admin user.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_database()
