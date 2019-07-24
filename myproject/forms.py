from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField, SelectMultipleField, DateField, RadioField, HiddenField
from wtforms.fields.html5 import TelField, TimeField
from wtforms.validators import InputRequired, Email, ValidationError, EqualTo

from myproject.models import User, Patient, Doctor, Receptionist, Schedule


class LoginForm(FlaskForm):
	email = StringField('Email', validators=[InputRequired(), Email()])
	password = PasswordField('Password', validators=[InputRequired()])

	remember_me = BooleanField('Remember me')

	login = SubmitField('Login')


class CheckEmail(object):
	def __init__(self, id_field=None):
		self.id_field = id_field
		self.id = -1
		self.message = 'This email has been registered already!'

	def __call__(self, form, field):
		if self.id_field is not None:
			self.id = form[self.id_field].data

		if User.query.filter(User.email==field.data, User.id!=self.id).first():
			raise ValidationError(self.message)


class CheckContact(object):
	def __init__(self, id_field=None):
		self.id_field = id_field
		self.id = -1
		self.message = 'This contact has been registered already!'

	def __call__(self, form, field):
		if self.id_field is not None:
			self.id = form[self.id_field].data

		if Patient.query.filter(Patient.contact==field.data, Patient.user_id!=self.id).first() or Doctor.query.filter(Doctor.contact==field.data, Doctor.user_id!=self.id).first() or Receptionist.query.filter(Receptionist.contact==field.data, Receptionist.user_id!=self.id).first():
			raise ValidationError(self.message)


class AddForm(FlaskForm):
	name = StringField(label='Name', validators=[InputRequired(message='This field cannot be left empty')])
	email = StringField(label='Email', validators=[InputRequired(message='This field cannot be left empty'), Email(), CheckEmail()])
	address = StringField(label='Address', validators=[InputRequired(message='This field cannot be left empty')])
	city = StringField(label='City')
	dob = DateField(label='DOB', format='%d/%m/%Y')
	gender = SelectField(label='Gender', choices=[('', 'Select a gender'), ('male', 'Male'), ('female', 'Female')], validators=[InputRequired()])
	contact = TelField(label='Contact', validators=[CheckContact()])

	submit = SubmitField(label='Submit')


class UpdateForm(FlaskForm):
	id = IntegerField(label='Id')
	name = StringField(label='Name', validators=[InputRequired(message='This field cannot be left empty')])
	email = StringField(label='Email', validators=[InputRequired(message='This field cannot be left empty'), Email(), CheckEmail('id')])
	address = StringField(label='Address', validators=[InputRequired(message='This field cannot be left empty')])
	city = StringField(label='City')
	dob = DateField(label='DOB', format='%d/%m/%Y')
	gender = SelectField(label='Gender', choices=[('', 'Select a gender'), ('male', 'Male'), ('female', 'Female')], validators=[InputRequired()])
	contact = TelField(label='Contact', validators=[ CheckContact('id')])


class AddDoctorForm(AddForm):
	specializations = SelectMultipleField(label='Specializations', coerce=int)
	degrees = SelectMultipleField(label='Degrees', coerce=int)


class UpdateDoctorForm(UpdateForm):
	specializations = SelectMultipleField(label='Specializations', coerce=int)
	degrees = SelectMultipleField(label='Degrees', coerce=int)


class ForgotPasswordForm(FlaskForm):
	email = StringField('Email', validators=[InputRequired(), Email()])

	send = SubmitField(label='Send Confirmation Link')


class ResetPasswordForm(FlaskForm):
	new_password = PasswordField('New Password', validators=[InputRequired(), EqualTo('confirm_pwd', message='Passwords do not match')])
	confirm_pwd =  PasswordField('Confirm Password', validators=[InputRequired()])

	submit = SubmitField(label='Submit')


class ChangePasswordForm(ResetPasswordForm):
	current_pwd = PasswordField('Current Password', validators=[InputRequired()])






