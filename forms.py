from flask_wtf import Form
from wtforms import TextField, PasswordField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class LoginForm(Form):
    username = TextField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

class AnswerForm(Form):
    answer = TextField("Answer", validators=[DataRequired()])

class PriceForm(Form):
    price = IntegerField("Price", validators=[DataRequired(), NumberRange(0)])
