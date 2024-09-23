# File: app/models/user.py

from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    accessible_tables = db.Column(db.String(256))
    permissions = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean, default=False)

    owned_tables = db.relationship('DynamicTable', back_populates='table_owner')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_access_table(self, table_name):
        if self.is_admin:
            return True
        accessible_tables = self.get_accessible_tables()
        owned_tables = [table.table_name for table in self.owned_tables]
        return table_name in accessible_tables or table_name in owned_tables

    def get_accessible_tables(self):
        return self.accessible_tables.split(',') if self.accessible_tables else []

    def can_view(self, table_name):
        return self.can_access_table(table_name) and 'view' in self.permissions.split(',')

    def can_edit(self, table_name):
        return self.can_access_table(table_name) and 'edit' in self.permissions.split(',')

    def can_create_tables(self):
        return self.is_admin or 'create' in self.permissions.split(',')
