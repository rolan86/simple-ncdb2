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

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_create_tables(self):
        return 'create' in self.permissions.split(',')

    def get_accessible_tables(self):
        return self.accessible_tables.split(',') if self.accessible_tables else []

    def can_view(self, table_name):
        return 'view' in self.permissions.split(',') and table_name in self.get_accessible_tables()

    def can_edit(self, table_name):
        return 'edit' in self.permissions.split(',') and table_name in self.get_accessible_tables()
