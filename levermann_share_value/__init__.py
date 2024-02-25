import logging
from logging.config import dictConfig

import babel
from flask import Flask, request, g
from flask_babel import Babel
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_apscheduler import APScheduler

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
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
})

metadata = MetaData(
    naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

db: SQLAlchemy = SQLAlchemy(metadata=metadata)

# initialize scheduler
scheduler = APScheduler()

def create_app() -> Flask:
    app = Flask(__name__, template_folder='templates')
    babel = Babel(app, locale_selector=get_locale)
    app.config['SECRET_KEY'] = 'dsfajifawo jflknvkdczxl'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['BABEL_LANGUAGES'] = ['en', 'de']  # Available languages
    app.config['BABEL_DEFAULT_LOCALE'] = 'de'  # Default locale
    app.config['SCHEDULER_API_ENABLED'] = True
    db.init_app(app)


    with app.app_context():
        db.create_all()
        logging.getLogger(__name__).info("Tables created")

    Migrate(app, db)
    from levermann_share_value.levermann.routes import routes
    app.register_blueprint(routes)

    # if you don't wanna use a config, you can set options here:
    # scheduler.api_enabled = True
    scheduler.init_app(app)
    scheduler.start()

    return app


def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(['de', 'fr', 'en'])