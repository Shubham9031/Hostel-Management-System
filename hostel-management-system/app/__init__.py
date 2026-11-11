from flask import Flask, render_template
from flask_login import LoginManager
from .config import Config
from .db import init_db
from .blueprints.auth import auth_bp
from .blueprints.dashboard import dashboard_bp
from .blueprints.students import students_bp
from .blueprints.rooms import rooms_bp
from .blueprints.allocations import allocations_bp
from .blueprints.fees import fees_bp
from .blueprints.mess import mess_bp
from .blueprints.complaints import complaints_bp
from .blueprints.leaves import leaves_bp
from .blueprints.visitors import visitors_bp
from .blueprints.notices import notices_bp
from .blueprints.reports import reports_bp

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    try:
        init_db(app)
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.get_by_id(user_id)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(allocations_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(mess_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(leaves_bp)
    app.register_blueprint(visitors_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(reports_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('shared/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('shared/500.html'), 500

    return app
