# File: app/models/table_relationship.py

from app import db

class TableRelationship(db.Model):
    __tablename__ = 'table_relationships'

    id = db.Column(db.Integer, primary_key=True)
    parent_table_id = db.Column(db.Integer, db.ForeignKey('dynamic_tables.id'), nullable=False)
    child_table_id = db.Column(db.Integer, db.ForeignKey('dynamic_tables.id'), nullable=False)
    relationship_type = db.Column(db.String(20), nullable=False)  # e.g., 'one-to-many', 'many-to-many'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    parent_table = db.relationship('DynamicTable', foreign_keys=[parent_table_id], backref=db.backref('child_relationships', lazy='dynamic'))
    child_table = db.relationship('DynamicTable', foreign_keys=[child_table_id], backref=db.backref('parent_relationships', lazy='dynamic'))

    def __repr__(self):
        return f'<TableRelationship {self.parent_table.table_name} -> {self.child_table.table_name}>'
