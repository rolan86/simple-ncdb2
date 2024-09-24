# File: app/routes/schema.py

import json, logging
import csv
from io import StringIO
from flask import send_file
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.schema_definition import SchemaDefinition
from app.models.table_relationship import TableRelationship
from app.models.dynamic_tables import get_all_dynamic_tables

bp = Blueprint('schema', __name__)

@bp.route('/manage_schemas')
@login_required
def manage_schemas():
    if not current_user.is_admin:
        flash('You do not have permission to manage schemas.', 'error')
        return redirect(url_for('main.dashboard'))

    schemas = SchemaDefinition.query.all()
    return render_template('schema/manage_schemas.html', schemas=schemas)

@bp.route('/create_schema', methods=['GET', 'POST'])
@login_required
def create_schema():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        structure = request.form.get('structure')  # This will be a JSON string

        if not name or not structure:
            flash('Name and structure are required.', 'error')
        else:
            new_schema = SchemaDefinition(name=name, description=description, structure=structure, owner_id=current_user.id)
            db.session.add(new_schema)
            db.session.commit()
            flash('Schema created successfully.', 'success')
            return redirect(url_for('schema.manage_schemas'))

    tables = get_all_dynamic_tables()
    return render_template('schema/create_schema.html', tables=tables)

@bp.route('/view_schema/<int:schema_id>')
@login_required
def view_schema(schema_id):
    schema = SchemaDefinition.query.get_or_404(schema_id)
    return render_template('schema/view_schema.html', schema=schema)

@bp.route('/edit_schema/<int:schema_id>', methods=['GET', 'POST'])
@login_required
def edit_schema(schema_id):
    schema = SchemaDefinition.query.get_or_404(schema_id)

    if schema.owner_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this schema.', 'error')
        return redirect(url_for('schema.manage_schemas'))

    if request.method == 'POST':
        # Create a new version of the schema
        new_schema = schema.create_new_version()

        new_schema.name = request.form['name']
        new_schema.description = request.form['description']

        # Process the relationships
        parents = request.form.getlist('parent[]')
        children = request.form.getlist('child[]')
        types = request.form.getlist('type[]')

        new_structure = []
        for parent, child, rel_type in zip(parents, children, types):
            if parent.strip() and child.strip() and rel_type.strip():
                new_structure.append({
                    'parent': parent.strip(),
                    'child': child.strip(),
                    'type': rel_type.strip()
                })

        if not new_structure:
            flash('At least one valid relationship is required.', 'error')
            return render_template('schema/edit_schema.html', schema=schema)

        new_schema.structure = json.dumps(new_structure)
        try:
            db.session.commit()
            flash('New schema version created successfully.', 'success')
            return redirect(url_for('schema.view_schema', schema_id=new_schema.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating schema: {str(e)}', 'error')
            return render_template('schema/edit_schema.html', schema=schema)

    return render_template('schema/edit_schema.html', schema=schema)

@bp.route('/delete_schema/<int:schema_id>', methods=['POST'])
@login_required
def delete_schema(schema_id):
    schema = SchemaDefinition.query.get_or_404(schema_id)
    db.session.delete(schema)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/schema_visualization/<int:schema_id>')
@login_required
def schema_visualization(schema_id):
    schema = SchemaDefinition.query.get_or_404(schema_id)

    logging.info(f"Schema structure: {schema.structure_json}")

    nodes = []
    links = []

    for relationship in schema.get_relationships():
        parent = relationship.get('parent')
        child = relationship.get('child')

        logging.info(f"Relationship: parent={parent}, child={child}")

        if parent and child:
            if parent not in nodes:
                nodes.append(parent)
            if child not in nodes:
                nodes.append(child)

            links.append({
                'source': nodes.index(parent),
                'target': nodes.index(child),
                'type': relationship.get('type', 'unknown')
            })

    result = {
        'nodes': [{'id': node} for node in nodes],
        'links': links
    }
    logging.info(f"Visualization data: {result}")
    return jsonify(result)

@bp.route('/schema_versions/<string:schema_name>')
@login_required
def schema_versions(schema_name):
    schemas = SchemaDefinition.query.filter_by(name=schema_name).order_by(SchemaDefinition.version.desc()).all()
    return render_template('schema/schema_versions.html', schemas=schemas, schema_name=schema_name)

@bp.route('/revert_schema/<int:schema_id>')
@login_required
def revert_schema(schema_id):
    schema = SchemaDefinition.query.get_or_404(schema_id)
    if schema.owner_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to revert this schema.', 'error')
        return redirect(url_for('schema.manage_schemas'))

    new_schema = schema.create_new_version()
    db.session.commit()
    flash(f'Reverted to schema version {schema.version}', 'success')
    return redirect(url_for('schema.view_schema', schema_id=new_schema.id))

@bp.route('/export_schema/<int:schema_id>')
@login_required
def export_schema(schema_id):
    schema = SchemaDefinition.query.get_or_404(schema_id)
    if schema.owner_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to export this schema.', 'error')
        return redirect(url_for('schema.manage_schemas'))

    data = {
        'name': schema.name,
        'description': schema.description,
        'structure': schema.structure,
        'version': schema.version
    }

    return jsonify(data)

@bp.route('/import_schema', methods=['GET', 'POST'])
@login_required
def import_schema():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file:
            try:
                data = json.load(file)
                new_schema = SchemaDefinition(
                    name=data['name'],
                    description=data['description'],
                    structure=data['structure'],
                    owner_id=current_user.id,
                    version=data['version']
                )
                db.session.add(new_schema)
                db.session.commit()
                flash('Schema imported successfully', 'success')
                return redirect(url_for('schema.view_schema', schema_id=new_schema.id))
            except Exception as e:
                flash(f'Error importing schema: {str(e)}', 'error')
    return render_template('schema/import_schema.html')
