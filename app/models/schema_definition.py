# File: app/models/schema_definition.py

from app import db
from sqlalchemy.types import JSON
import json

class SchemaDefinition(db.Model):
    __tablename__ = 'schema_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    structure = db.Column(JSON, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    version = db.Column(db.Integer, default=1, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('schema_definitions.id'))

    owner = db.relationship('User', backref=db.backref('owned_schemas', lazy='dynamic'))
    parent = db.relationship('SchemaDefinition', remote_side=[id], backref='children')

    __table_args__ = (db.UniqueConstraint('name', 'version', name='uq_schema_name_version'),)

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

    def create_new_version(self):
        new_version = SchemaDefinition(
            name=self.name,
            description=self.description,
            structure=self.structure,
            owner_id=self.owner_id,
            version=self.version + 1,
            parent_id=self.id
        )
        db.session.add(new_version)
        return new_version
