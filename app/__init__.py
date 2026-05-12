from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt
from app.config import Config
from flask_cors import CORS
from flask_migrate import Migrate


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

def create_app(config_class=Config):
    app =Flask(__name__)
    app.config.from_object(Config)

    # initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    from app.models import Teacher, Student, Department, Device, AttendanceLog, Report
    # Register bleprints here eg:
        #     from app.routes.auth import auth_bp
        #     app.register_blueprint(auth_bp, url_prefix='/api/auth')

    

    return app
