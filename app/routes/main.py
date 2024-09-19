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
    accessible_tables = current_user.accessible_tables.split(',') if current_user.accessible_tables else []
    return render_template('dashboard.html', tables=accessible_tables)
