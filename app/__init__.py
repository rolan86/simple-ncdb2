# File: app/__init__.py

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .routes import auth, main, data
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(data.bp)

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
