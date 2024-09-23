# File: app/routes/main.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    accessible_tables = current_user.get_accessible_tables()
    owned_tables = [table.table_name for table in current_user.owned_tables]
    all_tables = list(set(accessible_tables + owned_tables))

    return render_template('dashboard.html',
                           username=current_user.username,
                           tables=all_tables,
                           is_admin=current_user.is_admin)
