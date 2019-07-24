from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import InputRequired, Email, ValidationError

from myproject.models import Specialization, Degree
from myproject.forms import CheckEmail


class AccountForm(FlaskForm):
	id = IntegerField(label='Id')
	email = StringField(label='Email', validators=[InputRequired(message='This field cannot be left empty'), Email(), CheckEmail('id')])


class CheckSpecialization():
	def __init__(self):
		self.message = 'Specialization already present!'

	def __call__(self, form, field):
		if Specialization.query.filter_by(name=field.data).first():
			raise ValidationError(self.message)


class CheckDegree():
	def __init__(self):
		self.message = 'Degree already present!'

	def __call__(self, form, field):
		if Degree.query.filter_by(name=field.data).first():
			raise ValidationError(self.message)


class AddSpecializationForm(FlaskForm):
	new_specialization = StringField(label='Specialization', validators=[InputRequired(message='This field cannot be left empty'), CheckSpecialization()])

	add_btn = SubmitField(label='Add')


class AddDegreeForm(FlaskForm):
	new_degree = StringField(label='Degree', validators=[InputRequired(message='This field cannot be left empty'), CheckDegree()])

	add_btn = SubmitField(label='Add')


class AddRoleForm(FlaskForm):
	role = SelectField(label='Role', coerce=int)

	submit = SubmitField(label='Add')


