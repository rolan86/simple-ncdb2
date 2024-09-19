from app import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
import logging

# Dictionary to store our dynamic table classes
dynamic_table_classes = {}

def create_dynamic_table(table_name, columns):
    logging.info(f"Creating dynamic table: {table_name}")

    if table_name in dynamic_table_classes:
        logging.info(f"Table {table_name} already exists, returning existing class")
        return dynamic_table_classes[table_name]

    class DynamicTable(db.Model):
        __tablename__ = table_name
        id = Column(Integer, primary_key=True)
        core_uuid = Column(String(36), ForeignKey('core_table.uuid'), nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    for column_name, column_type in columns.items():
        if column_type == 'string':
            setattr(DynamicTable, column_name, Column(String(255)))
        elif column_type == 'integer':
            setattr(DynamicTable, column_name, Column(Integer))
        logging.info(f"Added column {column_name} of type {column_type} to {table_name}")

    # Store the newly created table class in our dictionary
    dynamic_table_classes[table_name] = DynamicTable

    logging.info(f"Dynamic table {table_name} created successfully")
    return DynamicTable

def get_table_class(table_name):
    logging.info(f"Attempting to get table class for: {table_name}")
    logging.info(f"Available dynamic tables: {list(dynamic_table_classes.keys())}")
    return dynamic_table_classes.get(table_name)

def get_all_dynamic_tables():
    return list(dynamic_table_classes.keys())

def ensure_dynamic_tables_exist():
    create_dynamic_table('employees', {
        'name': 'string',
        'position': 'string',
        'salary': 'integer'
    })

    create_dynamic_table('projects', {
        'name': 'string',
        'description': 'string',
        'status': 'string'
    })

    # Add any other dynamic tables here

    logging.info(f"Ensured existence of dynamic tables: {get_all_dynamic_tables()}")
