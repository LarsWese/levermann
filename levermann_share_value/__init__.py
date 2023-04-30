from flask import Flask
from logging.config import dictConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

db: SQLAlchemy = SQLAlchemy()

DB_NAME = "../instance/levermann.db"

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }, "file": {
        "class": "logging.FileHandler",
        "filename": "flask.log",
        "formatter": "default",
    }, "console": {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "default",
    }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
})


def create_app() -> Flask:
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = 'dsfajifawo jflknvkdczxl'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from levermann_share_value.database.models import Share
    with app.app_context():
        db.create_all()
        logging.getLogger(__name__).info("Tables created")

    Migrate(app, db)
    from levermann_share_value.levermann.routes import routes
    app.register_blueprint(routes)
    return app
