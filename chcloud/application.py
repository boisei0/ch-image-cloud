# encoding=utf-8
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from .jinja2_cloudinary_helper import CloudinaryTagExtension, CloudinaryURLExtension

db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from .models import User

    try:
        user_id = int(user_id)
    except ValueError:
        return None

    user = User.query.filter(User.id == user_id).first()

    if user:
        return user
    else:
        return None


def create_app(config):
    app = Flask(__name__)

    app.config.from_object(config)

    app.jinja_env.add_extension(CloudinaryURLExtension)
    app.jinja_env.add_extension(CloudinaryTagExtension)

    db.init_app(app)
    login_manager.init_app(app)

    from .views import OAuthRedirect, Index, Gallery
    app.add_url_rule('/', Index.endpoint, view_func=Index.as_view(Index.endpoint))
    app.add_url_rule('/slack/auth', OAuthRedirect.endpoint, view_func=OAuthRedirect.as_view(OAuthRedirect.endpoint))
    app.add_url_rule('/gallery', Gallery.endpoint, view_func=Gallery.as_view(Gallery.endpoint))

    return app
