from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt
from app.config import Config
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

metadata = MetaData(naming_convention={
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Import Blueprints
    from app.routes.attendance import attendance_bp
    from app.routes.auth import auth_bp
    from app.routes.departments import dept_bp
    from app.routes.students import students_bp
    from app.routes.reports import reports_bp 

    # Register Blueprints with leading slashes in prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(dept_bp, url_prefix='/departments')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app import models

    return app