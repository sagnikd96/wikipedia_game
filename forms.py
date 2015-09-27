from flask_wtf import Form
from wtforms import TextField, PasswordField, StringField, FileField
from wtforms.validators import DataRequired

class LoginForm(Form):
    username = TextField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

class AnswerForm(Form):
    answer = StringField("Answer", validators=[DataRequired()])

class SourceForm(Form):
    source = FileField("source")
