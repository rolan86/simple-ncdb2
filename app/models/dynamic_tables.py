# File: app/models/dynamic_tables.py

from app import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from datetime import datetime
import logging
from .dynamic_table import DynamicTable

def create_dynamic_table(table_name, columns, owner_id, is_independent=False):
    logging.info(f"Creating dynamic table: {table_name}")

    existing_table = DynamicTable.query.filter_by(table_name=table_name).first()
    if existing_table:
        logging.info(f"Table {table_name} already exists")
        return existing_table

    new_dynamic_table = DynamicTable(
        table_name=table_name,
        schema=columns,
        owner_id=owner_id,
        is_independent=is_independent
    )
    db.session.add(new_dynamic_table)
    db.session.commit()

    metadata = db.metadata
    table_columns = [
        Column('id', Integer, primary_key=True),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ]

    if not is_independent:
        table_columns.append(Column('core_uuid', String(36), ForeignKey('core_table.uuid'), nullable=False))

    for column_name, column_type in columns.items():
        if column_type == 'string':
            table_columns.append(Column(column_name, String(255)))
        elif column_type == 'integer':
            table_columns.append(Column(column_name, Integer))
        logging.info(f"Added column {column_name} of type {column_type} to {table_name}")

    table = Table(table_name, metadata, *table_columns)
    table.create(db.engine)
    logging.info(f"Dynamic table {table_name} created successfully")
    return new_dynamic_table

def get_table_class(table_name):
    logging.info(f"Attempting to get table class for: {table_name}")
    dynamic_table = DynamicTable.query.filter_by(table_name=table_name).first()
    if not dynamic_table:
        logging.info(f"Table {table_name} not found")
        return None

    metadata = db.metadata
    return Table(table_name, metadata, autoload_with=db.engine)

def get_all_dynamic_tables():
    return [table.table_name for table in DynamicTable.query.all()]

def ensure_dynamic_tables_exist(owner_id):
    tables_to_create = [
        ('employees', {
            'name': 'string',
            'position': 'string',
            'salary': 'integer'
        }),
        ('projects', {
            'name': 'string',
            'description': 'string',
            'status': 'string'
        })
    ]

    for table_name, columns in tables_to_create:
        existing_table = DynamicTable.query.filter_by(table_name=table_name).first()
        if not existing_table:
            create_dynamic_table(table_name, columns, owner_id=owner_id, is_independent=False)
            logging.info(f"Created dynamic table: {table_name}")
        else:
            logging.info(f"Dynamic table {table_name} already exists")

    logging.info(f"Ensured existence of dynamic tables: {get_all_dynamic_tables()}")
