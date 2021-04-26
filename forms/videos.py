from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, TextField, StringField
from wtforms.validators import DataRequired


class VideoForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    description = TextField("Описание", validators=[DataRequired()])
    authors = StringField("Авторы (короткие имена через ';')")
    video = FileField("Видео", validators=[FileRequired()])
    submit = SubmitField("Отправить")
