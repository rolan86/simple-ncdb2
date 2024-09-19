# File: seed.py

from app import create_app, db
from app.models.user import User
from app.models.dynamic_tables import create_dynamic_table
from werkzeug.security import generate_password_hash

def seed_database():
    app = create_app()
    with app.app_context():
        # Create users
        admin = User(username='admin', password_hash=generate_password_hash('admin123'), 
                     accessible_tables='users,employees,projects', permissions='view,edit,update')
        user1 = User(username='user1', password_hash=generate_password_hash('user123'), 
                     accessible_tables='employees,projects', permissions='view')
        user2 = User(username='user2', password_hash=generate_password_hash('user234'), 
                     accessible_tables='projects', permissions='view,edit')

        db.session.add_all([admin, user1, user2])
        db.session.commit()

        # Create dynamic tables
        employees_table = create_dynamic_table('employees', {
            'name': 'string',
            'position': 'string',
            'salary': 'integer'
        })

        projects_table = create_dynamic_table('projects', {
            'name': 'string',
            'description': 'string',
            'status': 'string'
        })

        # Add sample data
        emp1 = employees_table(name='John Doe', position='Developer', salary=75000)
        emp2 = employees_table(name='Jane Smith', position='Designer', salary=70000)
        
        proj1 = projects_table(name='Project A', description='First project', status='In Progress')
        proj2 = projects_table(name='Project B', description='Second project', status='Planning')

        db.session.add_all([emp1, emp2, proj1, proj2])
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
