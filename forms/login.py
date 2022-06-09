from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, BooleanField, SubmitField, IntegerField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    last_name = StringField('Отчество', validators=[DataRequired()])
    ryad = IntegerField('Номер ряда', validators=[DataRequired()])
    mesto = IntegerField('Номер места', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')