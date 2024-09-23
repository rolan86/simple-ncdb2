# File: init_db.py

from app import create_app, db
from app.models.user import User
from app.models.dynamic_table import DynamicTable
from app.models.core_table import CoreTable
from app.models.log import Log
from app.models.dynamic_tables import ensure_dynamic_tables_exist
from werkzeug.security import generate_password_hash
import logging
import uuid

def init_database():
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            logging.info("All tables created.")

            # Create admin user if not exists
            admin = create_admin_user()

            # Create core entries
            create_core_entries()

            # Ensure dynamic tables exist
            ensure_dynamic_tables_exist(admin.id)

            # Create regular users with specific table access
            create_regular_users(admin.id)

            logging.info("Database initialized successfully.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

def create_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            accessible_tables='',
            permissions='view,edit,update,create',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Admin user created.")

    # Update admin's accessible tables
    dynamic_tables = DynamicTable.query.all()
    admin.accessible_tables = ','.join([table.table_name for table in dynamic_tables])
    db.session.commit()
    logging.info("Admin user's accessible tables updated.")
    return admin

def create_core_entries():
    if CoreTable.query.first():
        logging.info("Core entries already exist. Skipping creation.")
        return

    core_entries = [
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Project Alpha',
            'description': 'A groundbreaking research project in quantum computing.'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Operation Beta',
            'description': 'Streamlining logistics for global supply chain optimization.'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Initiative Gamma',
            'description': 'Developing sustainable energy solutions for urban environments.'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Venture Delta',
            'description': 'Exploring applications of AI in healthcare diagnostics.'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Program Epsilon',
            'description': 'Implementing advanced cybersecurity measures for financial institutions.'
        }
    ]

    for entry in core_entries:
        core_item = CoreTable(**entry)
        db.session.add(core_item)

    db.session.commit()
    logging.info(f"{len(core_entries)} core entries created successfully.")

def create_regular_users(admin_id):
    users_data = [
        {
            'username': 'user1',
            'password': 'password1',
            'accessible_tables': 'employees',
            'permissions': 'view,edit'
        },
        {
            'username': 'user2',
            'password': 'password2',
            'accessible_tables': 'projects',
            'permissions': 'view'
        },
        {
            'username': 'user3',
            'password': 'password3',
            'accessible_tables': 'employees,projects',
            'permissions': 'view,edit,update'
        }
    ]

    for user_data in users_data:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            user = User(
                username=user_data['username'],
                password_hash=generate_password_hash(user_data['password']),
                accessible_tables=user_data['accessible_tables'],
                permissions=user_data['permissions'],
                is_admin=False
            )
            db.session.add(user)
            db.session.flush()  # This will assign an ID to the user

            # Log the user creation
            log_entry = Log(
                user_id=admin_id,
                action='create_user',
                table_name='users',
                entry_id=user.id,
                reason='Initial user setup'
            )
            db.session.add(log_entry)

    db.session.commit()
    logging.info("Regular users created successfully.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_database()
