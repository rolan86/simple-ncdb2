# File: init_db.py

from app import create_app, db
from app.models.user import User
from app.models.dynamic_table import DynamicTable
from app.models.core_table import CoreTable
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

            # Create core entries
            create_core_entries()

            # Ensure dynamic tables exist
            ensure_dynamic_tables_exist()

            # Update admin's accessible tables
            dynamic_tables = DynamicTable.query.all()
            admin.accessible_tables = ','.join([table.table_name for table in dynamic_tables])
            db.session.commit()

            logging.info("Database initialized successfully.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

def create_core_entries():
    # Check if core entries already exist
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_database()
