from flask import Flask, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)



    return app

from app import models