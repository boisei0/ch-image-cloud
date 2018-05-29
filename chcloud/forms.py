# encoding=utf-8
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import StringField, SelectMultipleField, validators, SubmitField, BooleanField


class Select2MultipleField(SelectMultipleField):
    def pre_validate(self, form):
        # Prevent "not a valid choice" error
        pass

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist
        else:
            self.data = []


class UploadForm(FlaskForm):
    image = FileField('Upload the photo: ', validators=[FileRequired()])
    title = StringField('Title/Description: ', validators=[validators.InputRequired()])
    tags = Select2MultipleField('Tags: ', render_kw={
        'multiple': 'multiple'
    })
    submit = SubmitField('Save')


class UploadEditForm(FlaskForm):
    title = StringField('Title/Description: ', validators=[validators.InputRequired()])
    tags = Select2MultipleField('Tags: ', render_kw={
        'multiple': 'multiple'
    })
    submit = SubmitField('Save')


class SettingsForm(FlaskForm):
    show_nsfw = BooleanField('Show NSFW content: ')
    submit = SubmitField('Save')
