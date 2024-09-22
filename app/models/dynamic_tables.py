# File: app/models/dynamic_tables.py

from app import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from datetime import datetime
import logging
from .dynamic_table import DynamicTable

def create_dynamic_table(table_name, columns):
    logging.info(f"Creating dynamic table: {table_name}")

    # Check if the table already exists
    existing_table = DynamicTable.query.filter_by(table_name=table_name).first()
    if existing_table:
        logging.info(f"Table {table_name} already exists, returning existing class")
        return get_table_class(table_name)

    # Create a new entry in the DynamicTable model
    new_dynamic_table = DynamicTable(table_name=table_name, schema=columns)
    db.session.add(new_dynamic_table)
    db.session.commit()

    # Create the actual table
    metadata = db.metadata
    table = Table(table_name, metadata,
        Column('id', Integer, primary_key=True),
        Column('core_uuid', String(36), ForeignKey('core_table.uuid'), nullable=False),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    for column_name, column_type in columns.items():
        if column_type == 'string':
            table.append_column(Column(column_name, String(255)))
        elif column_type == 'integer':
            table.append_column(Column(column_name, Integer))
        logging.info(f"Added column {column_name} of type {column_type} to {table_name}")

    table.create(db.engine)
    logging.info(f"Dynamic table {table_name} created successfully")
    return table

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

def ensure_dynamic_tables_exist():
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
        create_dynamic_table(table_name, columns)

    logging.info(f"Ensured existence of dynamic tables: {get_all_dynamic_tables()}")
