# File: app/models/dynamic_tables.py

from app import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
import logging

def create_dynamic_table(table_name, columns):
    logging.info(f"Creating dynamic table: {table_name}")
    
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
        # Add more types as needed
        logging.info(f"Added column {column_name} of type {column_type} to {table_name}")

    logging.info(f"Dynamic table {table_name} created successfully")
    return DynamicTable

def get_table_class(table_name):
    logging.info(f"Attempting to get table class for: {table_name}")
    for cls in db.Model.__subclasses__():
        if hasattr(cls, '__tablename__') and cls.__tablename__ == table_name:
            logging.info(f"Found table class for: {table_name}")
            return cls
    logging.warning(f"Table class not found for: {table_name}")
    return None
