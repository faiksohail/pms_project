from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField, SelectField, StringField
from wtforms.validators import InputRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed


class UploadTestForm(FlaskForm):
	test_id = HiddenField()
	test = FileField(label='Choose File', validators=[FileRequired(), FileAllowed(['jpeg', 'jpg', 'png', 'pdf'])])

	submit = SubmitField(label='Upload')


class AppointmentRequestForm(FlaskForm):
	doctor = SelectField(label='Doctor', choices=[(-1,'Choose a Doctor')], coerce=int, validators=[InputRequired()])
	date = StringField(label='Date', validators=[InputRequired()])
	visit_reason = StringField(label='Visit Reason', validators=[InputRequired()])

	submit = SubmitField(label='Submit')
