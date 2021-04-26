from flask_wtf import FlaskForm
from wtforms import SubmitField, TextField
from wtforms.validators import DataRequired


class CommentForm(FlaskForm):
    text = TextField("Комментарий", validators=[DataRequired()])
    submit = SubmitField("Комментировать")
