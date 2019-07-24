from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, BooleanField, SelectMultipleField, SelectField, RadioField, HiddenField, TextAreaField, FloatField
from wtforms.fields.html5 import DateField, TimeField
from wtforms.validators import InputRequired, Email, ValidationError, Optional

SYSTOLIC_CHOICES = [(0, 'Choose an Option')]
SYSTOLIC_CHOICES.extend([(i, i) for i in range(1, 241)])

DIASTOLIC_CHOICES = [(0, 'Choose an Option')]
DIASTOLIC_CHOICES.extend([(i, i) for i in range(1, 161)])


class MedicalRecordForm(FlaskForm):
	symptoms = StringField(label='Symptoms', validators=[Optional()])
	disease = StringField(label='Disease', validators=[Optional()])
	description = TextAreaField(label='Description', validators=[Optional()])

	submit = SubmitField(label='Add')


class VitalsForm(FlaskForm):
	bp_systolic = SelectField(label='BP Systolic', choices=SYSTOLIC_CHOICES, coerce=int, validators=[Optional()])
	bp_diastolic = SelectField(label='BP Diastolic', choices=DIASTOLIC_CHOICES, coerce=int, validators=[Optional()])
	temperature = FloatField(label='Temperature', validators=[Optional()])
	pulse = FloatField(label='Pulse', validators=[Optional()])
	weight = FloatField(label='Weight', validators=[Optional()])
	height = FloatField(label='Height', validators=[Optional()])

	submit = SubmitField(label='Add')


class PrescriptionForm(FlaskForm):
	name = StringField(label='Drug Name', validators=[InputRequired()])
	quantity = StringField(label='Quantity', validators=[InputRequired()])
	directions = StringField(label='Directions for Use', validators=[Optional()])

	submit = SubmitField(label='Add')


class TestOrderForm(FlaskForm):
	test_name = StringField(label='Test Name', validators=[InputRequired()])
	test_details = TextAreaField(label='Test Details', validators=[Optional()])

	submit = SubmitField(label='Add')


class SearchForm(FlaskForm):
	search = StringField(label='Search Patient', validators=[InputRequired()])
	filter = SelectField(choices=[('', 'filter by'), ('1', 'id'), ('2', 'email'), ('3', 'name')], validators=[InputRequired()])

	submit = SubmitField(label='Search')
