# encoding=utf-8
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config):
    app = Flask(__name__)

    app.config.from_object(config)
    db.init_app(app)

    from .views import OAuthRedirect
    app.add_url_rule('/slack/auth', OAuthRedirect.endpoint, view_func=OAuthRedirect.as_view(OAuthRedirect.endpoint))

    return app