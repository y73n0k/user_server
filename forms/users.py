from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    slug = StringField("Login (slug)", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    slug = StringField("Login (slug)", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_again = PasswordField("Repeat password", validators=[DataRequired()])
    submit = SubmitField("Submit")
