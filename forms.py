from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User
from wtforms import BooleanField  # Add this import at the top

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired("Email is required"),
        Email("Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired("Password is required")
    ])
    remember = BooleanField('Remember Me')  # Add this line
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')
    

class CVForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Save Changes')



class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired("Please enter your email address"),
        Email("Please enter a valid email address")
    ])


