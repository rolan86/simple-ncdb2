# File: init_db.py

from app import create_app, db
from app.models.user import User
from app.models.core_table import CoreTable
from app.models.dynamic_tables import create_dynamic_table
from werkzeug.security import generate_password_hash
import traceback

def init_database():
    app = create_app()
    with app.app_context():
        try:
            # Drop all existing tables
            db.drop_all()
            print("Existing tables dropped.")
            
            # Create all tables
            db.create_all()
            print("Base tables created.")
            
            # Create users
            admin = User(username='admin', 
                         password_hash=generate_password_hash('admin123'),
                         accessible_tables='employees,projects',
                         permissions='view,edit,update')
            user1 = User(username='user1',
                         password_hash=generate_password_hash('user123'),
                         accessible_tables='employees',
                         permissions='view')
            user2 = User(username='user2',
                         password_hash=generate_password_hash('user234'),
                         accessible_tables='projects',
                         permissions='view,edit')

            db.session.add_all([admin, user1, user2])
            db.session.commit()
            print("Users created.")

            # Create core table entries
            core1 = CoreTable(name='Core Entry 1', description='First core entry')
            core2 = CoreTable(name='Core Entry 2', description='Second core entry')
            db.session.add_all([core1, core2])
            db.session.commit()
            print("Core table entries created.")

            # Create dynamic tables
            try:
                EmployeesTable = create_dynamic_table('employees', {
                    'name': 'string',
                    'position': 'string',
                    'salary': 'integer'
                })
                print("Employees table created.")
            except Exception as e:
                print(f"Error creating Employees table: {str(e)}")
                print(traceback.format_exc())

            try:
                ProjectsTable = create_dynamic_table('projects', {
                    'name': 'string',
                    'description': 'string',
                    'status': 'string'
                })
                print("Projects table created.")
            except Exception as e:
                print(f"Error creating Projects table: {str(e)}")
                print(traceback.format_exc())

            # Create the dynamic tables in the database
            db.create_all()
            print("All tables created in the database.")

            # Add sample data
            try:
                emp1 = EmployeesTable(core_uuid=core1.uuid, name='John Doe', position='Developer', salary=75000)
                emp2 = EmployeesTable(core_uuid=core2.uuid, name='Jane Smith', position='Designer', salary=70000)
                
                proj1 = ProjectsTable(core_uuid=core1.uuid, name='Project A', description='First project', status='In Progress')
                proj2 = ProjectsTable(core_uuid=core2.uuid, name='Project B', description='Second project', status='Planning')

                db.session.add_all([emp1, emp2, proj1, proj2])
                db.session.commit()
                print("Sample data added.")
            except Exception as e:
                print(f"Error adding sample data: {str(e)}")
                print(traceback.format_exc())

            print("Database initialized and seeded successfully!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())

if __name__ == '__main__':
    init_database()
