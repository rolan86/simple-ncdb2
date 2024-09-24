# File: app/models/schema_definition.py

from app import db
from sqlalchemy.types import JSON
import json

class SchemaDefinition(db.Model):
    __tablename__ = 'schema_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    structure = db.Column(JSON, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    owner = db.relationship('User', backref=db.backref('owned_schemas', lazy='dynamic'))

    def __repr__(self):
        return f'<SchemaDefinition {self.name}>'

    @property
    def structure_json(self):
        """
        Returns the structure as a Python object.
        If structure is already a dict, return it directly.
        If it's a JSON string, parse it first.
        """
        if isinstance(self.structure, dict):
            return self.structure
        try:
            return json.loads(self.structure)
        except (TypeError, json.JSONDecodeError):
            return {}

    @structure_json.setter
    def structure_json(self, value):
        """
        Sets the structure, ensuring it's stored as JSON.
        If a dict is provided, it will be converted to a JSON string.
        """
        if isinstance(value, str):
            # Validate that the string is valid JSON
            json.loads(value)
            self.structure = value
        elif isinstance(value, dict):
            self.structure = json.dumps(value)
        else:
            raise ValueError("Structure must be a valid JSON string or a dictionary")

    def get_relationships(self):
        """
        Returns a list of relationships from the structure.
        """
        structure = self.structure_json
        return structure if isinstance(structure, list) else []
