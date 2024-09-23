from app import db
from sqlalchemy.types import JSON

class DynamicTable(db.Model):
    __tablename__ = 'dynamic_tables'

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(64), unique=True, nullable=False)
    schema = db.Column(JSON, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_independent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    table_owner = db.relationship('User', back_populates='owned_tables')

    def __repr__(self):
        return f'<DynamicTable {self.table_name}>'
