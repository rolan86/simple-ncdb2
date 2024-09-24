# File: app/routes/main.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.schema_definition import SchemaDefinition
from app.models.dynamic_table import DynamicTable

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    accessible_tables = current_user.get_accessible_tables()
    owned_tables = [table.table_name for table in current_user.owned_tables]
    all_tables = list(set(accessible_tables + owned_tables))

    # Fetch all schemas
    if current_user.is_admin:
        schemas = SchemaDefinition.query.all()
    else:
        # For non-admin users, fetch only the schemas they own
        schemas = SchemaDefinition.query.filter_by(owner_id=current_user.id).all()

    # Fetch table descriptions
    table_descriptions = {}
    for table in DynamicTable.query.all():
        schema_info = table.schema if table.schema else {}
        columns = ', '.join(schema_info.keys())
        table_descriptions[table.table_name] = f"Columns: {columns}"

    return render_template('dashboard.html',
                           username=current_user.username,
                           tables=all_tables,
                           table_descriptions=table_descriptions,
                           schemas=schemas,
                           is_admin=current_user.is_admin)
