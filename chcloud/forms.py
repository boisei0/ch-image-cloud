# encoding=utf-8
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import StringField, SelectField, validators


class Select2MultipleField(SelectField):
    def pre_validate(self, form):
        # Prevent "not a valid choice" error
        pass

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = ",".join(valuelist)
        else:
            self.data = ""


class UploadForm(FlaskForm):
    image = FileField('Upload the photo: ', validators=[FileRequired()])
    title = StringField('Title/Description: ', validators=[validators.InputRequired()])
    tags = Select2MultipleField('Tags: ', render_kw={
        'multiple': 'multiple'
    })


class UploadEditForm(FlaskForm):
    title = StringField('Title/Description: ', validators=[validators.InputRequired()])
    tags = Select2MultipleField('Tags: ', render_kw={
        'multiple': 'multiple'
    })
