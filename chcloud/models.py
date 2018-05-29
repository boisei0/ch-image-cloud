# encoding=utf-8
from collections import namedtuple

from flask_login import UserMixin

from .application import db


# uploads_tags = db.Table(
#     'uploads_tags',
#     db.MetaData,
#     db.Column('upload_id', db.Integer, db.ForeignKey('upload.id', onupdate='CASCADE', ondelete='CASCADE')),
#     db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', onupdate='CASCADE', ondelete='CASCADE'))
# )


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column('id', db.Integer, primary_key=True)
    display_name = db.Column('display_name', db.String(length=100), nullable=False)
    api_key = db.Column('slack_api_key', db.String(length=255), nullable=False)
    slack_id = db.Column('slack_user_id', db.String(length=15), unique=True, nullable=False)

    show_nsfw = db.Column('show_nsfw', db.Boolean(), default=False)

    # uploads = db.Relationship('Upload', back_populates='user')

    def __init__(self, display_name, api_key, slack_id, show_nsfw=False):
        self.display_name = display_name
        self.api_key = api_key
        self.slack_id = slack_id
        self.show_nsfw = show_nsfw

    def get_id(self):
        return str(self.id)

    @classmethod
    def from_tag(cls, tag_as_string):
        if tag_as_string.startswith('user:'):
            user = cls.query.filter(cls.slack_id == tag_as_string[5:]).first()
            if not user:
                raise ValueError('User not found')
            else:
                return user
        else:
            raise NotImplementedError

    @classmethod
    def from_context(cls, context_value_as_string, mock=False):
        _mock_user = namedtuple('User', ['id', 'display_name', 'slack_id', 'api_key', 'show_nsfw'])

        user = cls.query.filter(cls.slack_id == context_value_as_string).first()
        if not user:
            if mock:
                return _mock_user(-1, 'Unknown user', '', 'xoxp-undefined', False)
            else:
                raise ValueError('User not found')
        else:
            return user


# class Upload(db.Model):
#     __tablename__ = 'upload'
#     id = db.Column('id', db.Integer, primary_key=True)
#     access_name = db.Column('cloudinary_simple_name', db.String(length=100), nullable=False, unique=True)
#     title = db.Column('title', db.String(length=255), nullable=True)
#     file_hash = db.Column('file_hash', db.String(length=32), nullable=False, unique=True)
#
#     user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False)
#     user = db.Relationship('User', back_populates='uploads')
#     tags = db.Relationship('Tag', secondary=uploads_tags, back_populates='uploads')
#
#     def __init__(self, access_name, user_id, title=None):
#         self.access_name = access_name
#         self.user_id = user_id
#         self.title = title
#         self.file_hash = self._create_hash()
#
#     def _create_hash(self):
#         return hashlib.md5('{slack_user_id}.{access_name}'.format(
#             slack_user_id=self.user.slack_id,
#             access_name=self.access_name).encode('utf-8')
#         ).hexdigest()
#
#
# class Tag(db.Model):
#     __tablename__ = 'tag'
#     id = db.Column('id', db.Integer, primary_key=True)
#     tag = db.Column('tag', db.String(length=75), nullable=False, unique=True, index=True)
#
#     uploads = db.Relationship('Upload', secondary=uploads_tags, back_populates='tags')
#
#     def __init__(self, tag):
#         self.tag = tag
