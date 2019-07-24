import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import uuid

from myproject import db
from myproject.models import User, Patient, Doctor, Appointment, PatientRecord, PatientVital, PatientPrescription, PatientTest, TestReport, AppointmentRequest, Schedule
from myproject.forms import LoginForm, AddForm, UpdateForm, ChangePasswordForm
from myproject.patient.forms import UploadTestForm, AppointmentRequestForm
from myproject.utilities.permission import user_permission
from myproject.utilities.picture_handler import upload_picture, remove_picture
from myproject.utilities.mail_sender import send_email
from myproject.utilities.time_functions import day_of_week


patient_app = Blueprint('patient', __name__, template_folder='templates')


@patient_app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if current_user.is_authenticated:
		return redirect(url_for('patient.index'))

	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()

		if user is not None and user.check_password(form.password.data):
			login_user(user, remember=form.remember_me.data)

			next = request.args.get('next')
			if next is None or next[0] != '/':
				next = url_for('patient.index')

			return redirect(next)

		flash('Incorrect username or password')
		return render_template('patient/login.html', form=form)

	return render_template('patient/login.html', form=form)


@patient_app.route('/logout')
@login_required
@user_permission('patient')
def logout():

	logout_user()

	return redirect(url_for('patient.login'))


@patient_app.route('/account', methods=['GET', 'POST'])
@login_required
@user_permission('patient')
def account():
	form = UpdateForm()

	user = Patient.query.filter_by(user_id=current_user.id).first()

	if form.validate_on_submit():
		if current_user.email != form.email.data:
			code = str(uuid.uuid4())
			current_user.change_config = {
				'new_email': form.email.data,
				'confirm_code': code
			}

			form.email.data = current_user.email

			body_html = render_template('mail/confirm_email.html', user_id=current_user.id, confirm_code=code)
			body_text = render_template('mail/confirm_email.txt', user_id=current_user.id, confirm_code=code)

			# send_email(current_user.change_config['new_email'], 'Confirm your new email', body_html, body_text)

			flash('A verification link has been sent to this email')

		user.name = form.name.data
		user.gender = form.gender.data
		user.address = form.address.data
		user.city = form.city.data
		user.dob = form.dob.data
		user.contact = form.contact.data

		db.session.commit()

		flash('Records updated successfully!')

	elif request.method == 'GET':
		form.id.data = current_user.id
		form.email.data = current_user.email

		form.name.data = user.name
		form.gender.data = user.gender
		form.address.data = user.address
		form.city.data = user.city
		form.dob.data = user.dob
		form.contact.data = user.contact

	return render_template('patient/account.html', form=form, name=user.name)


@patient_app.route('/change_password', methods=['GET', 'POST'])
@login_required
@user_permission('patient')
def change_password():
	form = ChangePasswordForm()

	user = Patient.query.filter_by(user_id=current_user.id).first()

	if form.validate_on_submit():
		if current_user.check_password(form.current_pwd.data):
			if form.current_pwd.data != form.new_password.data:
				current_user.set_password(form.new_password.data)

				db.session.commit()

				return redirect(url_for('patient.index'))
			else:
				flash('You must use a new password!')
		else:
			flash('Incorrect password!')

	return render_template('patient/change_password.html', form=form, name=user.name)


@patient_app.route('/')
@patient_app.route('/index')
@login_required
@user_permission('patient')
def index():
	patient = Patient.query.filter_by(user_id=current_user.id).first()

	appointment_requests = AppointmentRequest.query.filter_by(patient_id=patient.id).order_by(AppointmentRequest.date.desc()).all()

	return render_template('patient/index.html', appointment_requests=appointment_requests)


@patient_app.route('/appointments')
@login_required
@user_permission('patient')
def appointments():
	patient = Patient.query.filter_by(user_id=current_user.id).first()

	appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.start_time.desc()).all()

	return render_template('patient/appointments.html', appointments=appointments)


@patient_app.route('/details/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@user_permission('patient')
def appointment_details(appointment_id):
	form = UploadTestForm()

	patient = Patient.query.filter_by(user_id=current_user.id).first()

	record = PatientRecord.query.filter_by(appointment_id=appointment_id, patient_id=patient.id).first()

	vital = PatientVital.query.filter_by(appointment_id=appointment_id, patient_id=patient.id).first()

	prescription = PatientPrescription.query.filter_by(appointment_id=appointment_id, patient_id=patient.id).all()

	test = PatientTest.query.filter_by(appointment_id=appointment_id, patient_id=patient.id).all()

	if form.validate_on_submit():
		if form.test.data:
			filename = upload_picture(form.test.data, current_user.id, form.test_id.data)

			report = TestReport(filename, form.test_id.data)
			report.save()

			return redirect(url_for('patient.appointment_details', appointment_id=appointment_id))

	return render_template('patient/appointment_details.html', record=record, vital=vital, prescription=prescription, test=test, form=form)


@patient_app.route('/delete_report/<int:report_id>')
@login_required
@user_permission('patient')
def delete_report(report_id):
	report = TestReport.query.filter_by(id=report_id).first()

	appointment_id = report.test.appointment_id

	boolean = remove_picture(report.filename)

	if boolean:
		db.session.delete(report)
		db.session.commit()

	return redirect(url_for('patient.appointment_details', appointment_id=appointment_id))


@patient_app.route('/doctors')
@login_required
@user_permission('patient')
def doctors():
	page = request.args.get('page', 1, type=int)

	doctors = Doctor.query.order_by(Doctor.user_id).paginate(page=page, per_page=6)

	return render_template('patient/doctors.html', doctors=doctors)


@patient_app.route('/doctor_details/<int:doctor_id>')
@login_required
@user_permission('patient')
def doctor_details(doctor_id):

	doctor = Doctor.query.filter_by(id=doctor_id).first()

	return render_template('patient/doctor_details.html', doctor=doctor)


@patient_app.route('/appointment_request', methods=['GET', 'POST'])
@login_required
@user_permission('patient')
def appointment_request():
	form = AppointmentRequestForm()

	patient = Patient.query.filter_by(user_id=current_user.id).first()

	doctors = db.session.query(Doctor.id, Doctor.name).join(Schedule).filter(Schedule.day==day_of_week()).all()
	form.doctor.choices.extend(doctors)

	if form.validate_on_submit():
		appointment_rqst = AppointmentRequest(form.date.data, form.visit_reason.data, patient.id, form.doctor.data)
		appointment_rqst.save()

		return redirect(url_for('patient.index'))

	elif request.method == 'GET':
		form.date.data = datetime.today().date()

	return render_template('patient/appointment_request.html', form=form)


@patient_app.route('/appointment_request/<int:request_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('patient')
def delete_request(request_id):
	appointment_request = AppointmentRequest.query.filter_by(id=request_id).first()

	db.session.delete(appointment_request)
	db.session.commit()

	return redirect(url_for('patient.index'))
