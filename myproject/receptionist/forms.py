from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField, HiddenField
from wtforms.fields.html5 import TimeField
from wtforms.validators import InputRequired, ValidationError

from myproject.models import Schedule

class CheckTime(object):
	def __init__(self, time_field):
		self.time_field = time_field

	def __call__(self, form, field):
		if field.data < form[self.time_field].data:
			raise ValidationError("End time can't have a value less than start time")


class ScheduleForm(FlaskForm):
	day = SelectField(label='Days', choices=[('', 'Choose a day'), ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
												('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')], validators=[InputRequired()])
	start_time = TimeField(label='Start time', validators=[InputRequired()])
	end_time = TimeField(label='End time', validators=[InputRequired(), CheckTime('start_time')])

	submit = SubmitField(label="Add")


class AddAppointmentForm(FlaskForm):
	doctor = HiddenField(label="Doctor id")
	patient = SelectField(label='Patient', choices=[(-1,'Choose a Patient')], coerce=int, validators=[InputRequired()])
	date = StringField(label='Date', validators=[InputRequired()])
	start_time = TimeField(label='Start Time', validators=[InputRequired()])
	slot = SelectField(label='Slot', choices=[(5*i, 5*i) for i in range(1,7)], coerce=int)

	submit = SubmitField(label="Add")


class UpdateAppointmentForm(FlaskForm):
	doctor = HiddenField(label="Doctor id")
	patient = SelectField(label='Patient', choices=[(-1, 'Choose a Patient')], coerce=int, validators=[InputRequired()])
	date = StringField(label='Date')
	start_time = TimeField(label='Start Time')
	slot = SelectField(label='Slot', choices=[(5 * i, 5 * i) for i in range(1, 7)], coerce=int)
	end_time = TimeField(label='End Time')
	status = RadioField(label='Status', choices=[(0, 'Pending'), (1, 'Checked'), (2,'Cancelled')], coerce=int)





