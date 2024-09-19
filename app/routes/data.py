# File: app/routes/data.py

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.dynamic_tables import get_table_class
from sqlalchemy import inspect
from app.models.core_table import CoreTable
from sqlalchemy.orm import aliased


bp = Blueprint('data', __name__)

@bp.route('/view_table/<table_name>')
@login_required
def view_table(table_name):
    if table_name not in (current_user.accessible_tables or '').split(','):
        flash('You do not have permission to view this table.', 'error')
        return redirect(url_for('main.dashboard'))
    
    Table = get_table_class(table_name)
    if not Table:
        flash(f'Dynamic table {table_name} not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Query the dynamic table
        dynamic_data = db.session.query(Table).all()
        
        # Query the core table
        core_data = db.session.query(CoreTable).all()
        
        # Combine the data
        combined_data = []
        for entry in dynamic_data:
            core_entry = next((core for core in core_data if core.uuid == entry.core_uuid), None)
            combined_data.append((entry, core_entry))
        
        columns = [column.name for column in Table.__table__.columns if column.name not in ['id', 'core_uuid', 'created_at', 'updated_at']]
        core_columns = ['name', 'description']
        
        return render_template('data/table_view.html', 
                               table_name=table_name, 
                               data=combined_data, 
                               columns=columns,
                               core_columns=core_columns,
                               user_permissions=current_user.permissions.split(','),
                               user_tables=current_user.accessible_tables.split(','),
                               all_core_entries=core_data)
    except Exception as e:
        flash(f'Error querying data: {str(e)}', 'error')
        return render_template('data/table_view.html', 
                               table_name=table_name, 
                               data=[], 
                               columns=[],
                               core_columns=['name', 'description'],
                               user_permissions=current_user.permissions.split(','),
                               user_tables=current_user.accessible_tables.split(','),
                               all_core_entries=[])

@bp.route('/edit_entry/<table_name>/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(table_name, entry_id):
    if 'edit' not in current_user.permissions or table_name not in (current_user.accessible_tables or '').split(','):
        flash('You do not have permission to edit this table.', 'error')
        return redirect(url_for('main.dashboard'))
    
    Table = get_table_class(table_name)
    if not Table:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    entry = db.session.query(Table).get(entry_id)
    if not entry:
        flash('Entry not found.', 'error')
        return redirect(url_for('data.view_table', table_name=table_name))
    
    core_entry = db.session.query(CoreTable).filter_by(uuid=entry.core_uuid).first()
    
    if request.method == 'POST':
        for column in Table.__table__.columns:
            if column.name not in ['id', 'core_uuid', 'created_at', 'updated_at']:
                setattr(entry, column.name, request.form.get(column.name))
        db.session.commit()
        flash('Entry updated successfully.', 'success')
        return redirect(url_for('data.view_table', table_name=table_name))
    
    return render_template('data/edit_entry.html', table_name=table_name, entry=entry, core_entry=core_entry)

@bp.route('/add_entry/<table_name>', methods=['GET', 'POST'])
@login_required
def add_entry(table_name):
    if 'edit' not in current_user.permissions or table_name not in (current_user.accessible_tables or '').split(','):
        flash('You do not have permission to add entries to this table.', 'error')
        return redirect(url_for('main.dashboard'))
    
    Table = get_table_class(table_name)
    if not Table:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        core_uuid = request.form.get('core_uuid')
        if not core_uuid:
            flash('Core entry must be selected.', 'error')
            return redirect(url_for('data.add_entry', table_name=table_name))

        new_entry = Table(core_uuid=core_uuid)
        for column in Table.__table__.columns:
            if column.name not in ['id', 'core_uuid', 'created_at', 'updated_at']:
                setattr(new_entry, column.name, request.form.get(column.name))
        db.session.add(new_entry)
        db.session.commit()
        flash('New entry added successfully.', 'success')
        return redirect(url_for('data.view_table', table_name=table_name))
    
    columns = [column for column in Table.__table__.columns if column.name not in ['id', 'core_uuid', 'created_at', 'updated_at']]
    core_entries = db.session.query(CoreTable).all()
    return render_template('data/add_entry.html', table_name=table_name, columns=columns, core_entries=core_entries)

def get_table_data(table_name):
    Table = get_table_class(table_name)
    if Table:
        return [row.__dict__ for row in db.session.query(Table).all()]
    return []

def get_table_schema(table_name):
    Table = get_table_class(table_name)
    if Table:
        return {c.name: str(c.type) for c in Table.__table__.columns}
    return {}

# CRUD operations

@bp.route('/create/<table_name>', methods=['POST'])
@login_required
def create_entry(table_name):
    if table_name not in (current_user.accessible_tables or '').split(','):
        return jsonify({'error': 'Permission denied'}), 403
    
    Table = get_table_class(table_name)
    if not Table:
        return jsonify({'error': 'Table not found'}), 404

    data = request.json
    new_entry = Table(**data)
    db.session.add(new_entry)
    db.session.commit()
    return jsonify({'message': 'Entry created successfully'}), 201

@bp.route('/update/<table_name>/<int:entry_id>', methods=['PUT'])
@login_required
def update_entry(table_name, entry_id):
    if table_name not in (current_user.accessible_tables or '').split(','):
        return jsonify({'error': 'Permission denied'}), 403
    
    Table = get_table_class(table_name)
    if not Table:
        return jsonify({'error': 'Table not found'}), 404

    entry = db.session.query(Table).get(entry_id)
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    data = request.json
    for key, value in data.items():
        setattr(entry, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Entry updated successfully'}), 200

@bp.route('/delete/<table_name>/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_entry(table_name, entry_id):
    if table_name not in (current_user.accessible_tables or '').split(','):
        return jsonify({'error': 'Permission denied'}), 403
    
    Table = get_table_class(table_name)
    if not Table:
        return jsonify({'error': 'Table not found'}), 404

    entry = db.session.query(Table).get(entry_id)
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Entry deleted successfully'}), 200

@bp.route('/list_tables')
@login_required
def list_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    return jsonify({'tables': tables})

@bp.route('/debug_table/<table_name>')
@login_required
def debug_table(table_name):
    Table = get_table_class(table_name)
    if not Table:
        return jsonify({'error': 'Table not found'}), 404
    
    data = db.session.query(Table).all()
    result = [row.__dict__ for row in data]
    
    # Remove SQLAlchemy instance state
    for row in result:
        row.pop('_sa_instance_state', None)
    
    return jsonify(result)
