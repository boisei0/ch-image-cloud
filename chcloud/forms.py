# encoding=utf-8
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import StringField, validators


class UploadForm(FlaskForm):
    image = FileField('Upload the photo: ', validators=[FileRequired()])
    title = StringField('Title/Description: ', validators=[validators.InputRequired()])
