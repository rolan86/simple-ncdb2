# File: app/routes/data.py

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.dynamic_tables import create_dynamic_table, get_table_class, get_all_dynamic_tables
from app.models.log import Log
from app.models.user import User
from app.models.dynamic_table import DynamicTable
from sqlalchemy import inspect, insert, select, update, Table, Column
from app.models.core_table import CoreTable
from sqlalchemy.orm import aliased
import logging


bp = Blueprint('data', __name__)

from app.models.dynamic_tables import get_table_class
from app.models.core_table import CoreTable
from sqlalchemy.orm import aliased

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@bp.route('/view_table/<table_name>')
@login_required
def view_table(table_name):
    print(f"Accessing view_table for table: {table_name}")
    if not current_user.can_access_table(table_name):
        flash('You do not have permission to view this table.', 'error')
        return redirect(url_for('main.dashboard'))

    Table = get_table_class(table_name)
    if Table is None:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        # Fetch data from the dynamic table
        stmt = select(Table)
        print(f"SQL Query: {stmt}")

        result = db.session.execute(stmt)

        # Print raw query result
        raw_result = list(result)
        print(f"Raw query result: {raw_result}")

        data = []
        columns = [column.name for column in Table.columns
                   if column.name not in ['created_at', 'updated_at']]  # Include 'id' in columns

        print(f"Columns for table {table_name}: {columns}")

        for row in raw_result:
            row_dict = {}
            for i, column in enumerate(Table.columns):
                if column.name in columns:
                    row_dict[column.name] = str(row[i]) if row[i] is not None else ''

            print(f"Processed row data: {row_dict}")

            core_entry = None
            if 'core_uuid' in row_dict and row_dict['core_uuid']:
                core_entry = CoreTable.query.filter_by(uuid=row_dict['core_uuid']).first()
                print(f"Core entry found: {core_entry}")

            core_data = core_entry.to_dict() if core_entry else {}
            print(f"Core data: {core_data}")

            data.append((row_dict, core_data))

        core_columns = ['name', 'description']

        print(f"Final data: {data}")
        print(f"Core columns: {core_columns}")

        return render_template('data/table_view.html',
                               table_name=table_name,
                               data=data,
                               columns=columns,
                               core_columns=core_columns,
                               user_permissions=current_user.permissions.split(','),
                               user_tables=current_user.get_accessible_tables())
    except Exception as e:
        print(f"Error viewing table {table_name}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f'Error viewing table: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@bp.route('/select_view/<table_name>')
@login_required
def select_view(table_name):
    if table_name not in current_user.get_accessible_tables():
        flash('You do not have permission to view this table.', 'error')
        return redirect(url_for('main.dashboard'))

    return render_template('data/select_view.html', table_name=table_name)

@bp.route('/view_data/<table_name>/<view_type>')
@login_required
def view_data(table_name, view_type):
    if table_name not in current_user.get_accessible_tables():
        flash('You do not have permission to view this table.', 'error')
        return redirect(url_for('main.dashboard'))

    Table = get_table_class(table_name)
    if Table is None:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))

    CoreTableAlias = aliased(CoreTable)
    data = db.session.query(Table, CoreTableAlias).outerjoin(
        CoreTableAlias, Table.core_uuid == CoreTableAlias.uuid
    ).all()

    columns = [column.name for column in Table.columns
               if column.name not in ['id', 'core_uuid', 'created_at', 'updated_at']]
    core_columns = ['name', 'description']

    return render_template(f'data/{view_type}_view.html',
                           table_name=table_name,
                           data=data,
                           columns=columns,
                           core_columns=core_columns,
                           user_permissions=current_user.permissions.split(','))

@bp.route('/add_entry/<table_name>', methods=['GET', 'POST'])
@login_required
def add_entry(table_name):
    if 'edit' not in current_user.permissions.split(',') or not current_user.can_access_table(table_name):
        flash('You do not have permission to add entries to this table.', 'error')
        return redirect(url_for('main.dashboard'))

    dynamic_table = DynamicTable.query.filter_by(table_name=table_name).first()
    if dynamic_table is None:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))

    Table = get_table_class(table_name)
    if Table is None:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))

    core_entries = CoreTable.query.all() if not dynamic_table.is_independent else []

    if request.method == 'POST':
        new_entry = {}
        for column in Table.columns:
            if column.name not in ['id', 'created_at', 'updated_at']:
                new_entry[column.name] = request.form.get(column.name)

        if not dynamic_table.is_independent:
            new_entry['core_uuid'] = request.form.get('core_uuid')

        reason = request.form.get('reason')
        if not reason:
            flash('Please provide a reason for this entry.', 'error')
            return render_template('data/add_entry.html', table_name=table_name, columns=Table.columns, core_entries=core_entries, is_independent=dynamic_table.is_independent)

        try:
            stmt = insert(Table).values(**new_entry)
            result = db.session.execute(stmt)
            db.session.commit()

            log_entry = Log(user_id=current_user.id, action='add', table_name=table_name,
                            entry_id=result.inserted_primary_key[0], reason=reason)
            db.session.add(log_entry)
            db.session.commit()

            flash('New entry added successfully.', 'success')
            return redirect(url_for('data.view_table', table_name=table_name))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding entry: {str(e)}', 'error')

    columns = [column for column in Table.columns if column.name not in ['id', 'created_at', 'updated_at']]
    return render_template('data/add_entry.html', table_name=table_name, columns=columns, core_entries=core_entries, is_independent=dynamic_table.is_independent)

@bp.route('/edit_entry/<table_name>/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(table_name, entry_id):
    if 'edit' not in current_user.permissions.split(',') or table_name not in current_user.get_accessible_tables():
        flash('You do not have permission to edit entries in this table.', 'error')
        return redirect(url_for('main.dashboard'))

    Table = get_table_class(table_name)
    if Table is None:
        flash('Table not found.', 'error')
        return redirect(url_for('main.dashboard'))

    stmt = select(Table).where(Table.c.id == entry_id)
    result = db.session.execute(stmt).first()

    if result is None:
        flash('Entry not found.', 'error')
        return redirect(url_for('data.view_table', table_name=table_name))

    columns = [column for column in Table.columns
               if column.name not in ['id', 'core_uuid', 'created_at', 'updated_at']]

    if request.method == 'POST':
        reason = request.form.get('reason')
        if not reason:
            flash('Please provide a reason for this edit.', 'error')
            entry = {column.name: getattr(result, column.name) for column in Table.columns}
            return render_template('data/edit_entry.html', table_name=table_name, entry=entry, columns=columns)

        try:
            update_data = {}
            for column in columns:
                update_data[column.name] = request.form.get(column.name)

            stmt = update(Table).where(Table.c.id == entry_id).values(**update_data)
            db.session.execute(stmt)

            # Log the action
            log_entry = Log(user_id=current_user.id, action='edit', table_name=table_name,
                            entry_id=entry_id, reason=reason)
            db.session.add(log_entry)
            db.session.commit()

            flash('Entry updated successfully.', 'success')
            return redirect(url_for('data.view_table', table_name=table_name))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating entry: {str(e)}")
            flash(f'Error updating entry: {str(e)}', 'error')

    entry = {column.name: getattr(result, column.name) for column in Table.columns}
    return render_template('data/edit_entry.html', table_name=table_name, entry=entry, columns=columns)

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
    if Table is None:
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
    if Table is None:
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
    if Table is None:
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

@bp.route('/debug/tables')
def debug_tables():
    from app.models.dynamic_tables import get_all_dynamic_tables
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    all_tables = inspector.get_table_names()
    dynamic_tables = get_all_dynamic_tables()

    return jsonify({
        'all_tables': all_tables,
        'dynamic_tables': dynamic_tables,
    })

# In app/routes/data.py

@bp.route('/create_dynamic_table', methods=['GET', 'POST'])
@login_required
def create_dynamic_table_route():
    if not current_user.can_create_tables():
        flash('You do not have permission to create tables.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        table_name = request.form.get('table_name')
        columns = {}
        for i in range(1, 6):  # Allow up to 5 columns
            column_name = request.form.get(f'column_name_{i}')
            column_type = request.form.get(f'column_type_{i}')
            if column_name and column_type:
                columns[column_name] = column_type

        owner_id = int(request.form.get('owner_id'))
        is_independent = request.form.get('is_independent') == 'on'

        if not table_name or not columns:
            flash('Table name and at least one column are required.', 'error')
        else:
            try:
                new_table = create_dynamic_table(table_name, columns, owner_id=owner_id, is_independent=is_independent)

                # Update owner's accessible tables
                owner = User.query.get(owner_id)
                if owner:
                    accessible_tables = set(owner.get_accessible_tables())
                    accessible_tables.add(table_name)
                    owner.accessible_tables = ','.join(accessible_tables)
                    db.session.commit()

                flash(f'Dynamic table "{table_name}" created successfully.', 'success')
                return redirect(url_for('data.create_dynamic_table_route'))
            except Exception as e:
                flash(f'Error creating table: {str(e)}', 'error')

    users = User.query.all()  # Get all users for the owner selection dropdown
    existing_tables = get_all_dynamic_tables()
    return render_template('data/create_dynamic_table.html', existing_tables=existing_tables, users=users)

@bp.route('/update_entries/<table_name>', methods=['PUT'])
@login_required
def update_entries(table_name):
    if 'edit' not in current_user.permissions.split(',') or table_name not in current_user.get_accessible_tables():
        return jsonify({'error': 'Permission denied'}), 403

    Table = get_table_class(table_name)
    if Table is None:
        return jsonify({'error': 'Table not found'}), 404

    data = request.json
    try:
        for entry in data:
            row = db.session.query(Table).filter_by(id=entry['id']).first()
            if row:
                for key, value in entry.items():
                    if key != 'id' and hasattr(row, key):
                        setattr(row, key, value)
        db.session.commit()
        return jsonify({'message': 'Entries updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
