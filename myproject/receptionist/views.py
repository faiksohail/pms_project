from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import uuid

from myproject import db
from myproject.models import Patient, Doctor, User, Role, Specialization, Degree, Receptionist, Schedule, Appointment, AppointmentRequest
from myproject.forms import LoginForm, AddForm, UpdateForm, AddDoctorForm, UpdateDoctorForm, ChangePasswordForm
from myproject.receptionist.forms import AddAppointmentForm, UpdateAppointmentForm, ScheduleForm
from myproject.utilities.permission import user_permission
from myproject.utilities.password_generator import generate_random_password
from myproject.utilities.mail_sender import send_email
from myproject.utilities.time_functions import day_of_week, add_time

receptionist_app = Blueprint('receptionist', __name__, template_folder='templates')


@receptionist_app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if current_user.is_authenticated:
		return redirect(url_for('receptionist.index'))

	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()

		if user is not None and user.check_password(form.password.data):
			login_user(user, remember=form.remember_me.data)

			next = request.args.get('next')
			if next is None or next[0] != '/':
				next = url_for('receptionist.index')

			return redirect(next)

		flash('Incorrect username or password')
		return render_template('receptionist/login.html', form=form)

	return render_template('receptionist/login.html', form=form)


@receptionist_app.route('/logout')
@login_required
@user_permission('receptionist')
def logout():

	logout_user()

	return redirect(url_for('receptionist.login'))


@receptionist_app.route('/account', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def account():
	form = UpdateForm()

	user = Receptionist.query.filter_by(user_id=current_user.id).first()

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

	return render_template('receptionist/account.html', form=form, name=user.name)


@receptionist_app.route('/change_password', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def change_password():
	form = ChangePasswordForm()

	user = Receptionist.query.filter_by(user_id=current_user.id).first()

	if form.validate_on_submit():
		if current_user.check_password(form.current_pwd.data):
			if form.current_pwd.data != form.new_password.data:
				current_user.set_password(form.new_password.data)

				db.session.commit()

				return redirect(url_for('receptionist.index'))
			else:
				flash('You must use a new password!')
		else:
			flash('Incorrect password!')

	return render_template('receptionist/change_password.html', form=form, name=user.name)


@receptionist_app.route('/')
@receptionist_app.route('/index')
@login_required
@user_permission('receptionist')
def index():

	return render_template('receptionist/index.html')


######################################################################################
################################### Patient ##########################################
######################################################################################
@receptionist_app.route('/patient/add', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def add_patient():
	form = AddForm()

	if form.validate_on_submit():
		email = form.email.data
		password = generate_random_password()

		name = form.name.data
		gender = form.gender.data
		address = form.address.data
		city = form.city.data
		dob = form.dob.data
		contact = form.contact.data

		user = User(email, password)
		patient_role = Role.get_role('patient')

		user.save()
		user.add_role(patient_role)

		user_id = user.id
		patient = Patient(name, gender, address, city, dob, contact, user_id)
		patient.save()

		body_html = render_template('mail/staff_credentials.html', email=email, password=password)
		body_text = render_template('mail/staff_credentials.txt', email=email, password=password)

		# send_email(email, 'Welcome to PMS', body_html, body_text)

		return redirect(url_for('receptionist.list_patient'))

	return render_template('receptionist/add_patient.html', form=form)


@receptionist_app.route('/patient/list')
@login_required
@user_permission('receptionist')
def list_patient():
	patients = Patient.query.order_by(Patient.user_id.desc()).all()

	return render_template('receptionist/list_patient.html', patients=patients)


@receptionist_app.route('/patient/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def patient_details(user_id):
	form = UpdateForm()

	patient = Patient.query.filter_by(user_id=user_id).first()

	if patient is None:
		flash('Invalid Path!!!')
		abort(404)

	if form.validate_on_submit():
		if patient.user.email != form.email.data:
			code = str(uuid.uuid4())
			patient.user.change_config = {
				'new_email': form.email.data,
				'confirm_code': code
			}

			form.email.data = patient.user.email

			body_html = render_template('mail/confirm_email.html', user_id=patient.user_id, confirm_code=code)
			body_text = render_template('mail/confirm_email.txt', user_id=patient.user_id, confirm_code=code)

			# send_email(patient.user.change_config['new_email'], 'Confirm your new email', body_html, body_text)

			flash('A verification link has been sent to this email')

		patient.name = form.name.data
		patient.gender = form.gender.data
		patient.address = form.address.data
		patient.city = form.city.data
		patient.dob = form.dob.data
		patient.contact = form.contact.data

		db.session.commit()

		flash('Records updated successfully!')

	elif request.method == 'GET':
		form.id.data = patient.user.id
		form.email.data = patient.user.email

		form.name.data = patient.name
		form.gender.data = patient.gender
		form.address.data = patient.address
		form.city.data = patient.city
		form.dob.data = patient.dob
		form.contact.data = patient.contact

	return render_template('receptionist/patient_details.html', patient=patient, form=form)


@receptionist_app.route('/patient/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def delete_patient(user_id):
	user = User.query.filter_by(id=user_id).first()
	patient = Patient.query.filter_by(user_id=user_id).first()

	db.session.delete(patient)
	db.session.delete(user)

	db.session.commit()

	return redirect(url_for('receptionist.list_patient'))


######################################################################################
#################################### Doctor ##########################################
######################################################################################
@receptionist_app.route('/doctor/add', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def add_doctor():
	form = AddDoctorForm()

	form.specializations.choices = Specialization.specialization_choices()
	form.degrees.choices = Degree.degree_choices()

	if form.validate_on_submit():
		email = form.email.data
		password = generate_random_password()

		name = form.name.data
		gender = form.gender.data
		address = form.address.data
		city = form.city.data

		specialization_ids = form.specializations.data
		degree_ids = form.degrees.data

		dob = form.dob.data
		contact = form.contact.data

		user = User(email, password)

		doctor_role = Role.get_role('doctor')

		user.save()
		user.add_role(doctor_role)

		user_id = user.id
		doctor = Doctor(name, gender, address, city, dob, contact, user_id)

		specializations = [Specialization.query.get(i) for i in specialization_ids]
		degrees = [Degree.query.get(i) for i in degree_ids]

		doctor.add_specializations(specializations)
		doctor.add_degrees(degrees)

		doctor.save()

		body_html = render_template('mail/staff_credentials.html', email=email, password=password)
		body_text = render_template('mail/staff_credentials.txt', email=email, password=password)

		# send_email(email, 'Welcome to PMS', body_html, body_text)

		return redirect(url_for('receptionist.list_doctor'))

	return render_template('receptionist/add_doctor.html', form=form)


@receptionist_app.route('/doctor/list')
@login_required
@user_permission('receptionist')
def list_doctor():
	doctors = Doctor.query.order_by(Doctor.user_id.desc()).all()

	return render_template('receptionist/list_doctor.html', doctors=doctors)


@receptionist_app.route('/doctor/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def doctor_details(user_id):
	form = UpdateDoctorForm()

	doctor = Doctor.query.filter_by(user_id=user_id).first()

	form.specializations.choices = Specialization.specialization_choices()
	form.degrees.choices = Degree.degree_choices()

	if doctor is None:
		flash('Invalid Path!!!')
		abort(404)

	if form.validate_on_submit():
		if doctor.user.email != form.email.data:
			code = str(uuid.uuid4())
			doctor.user.change_config = {
				'new_email': form.email.data,
				'confirm_code': code
			}

			form.email.data = doctor.user.email

			body_html = render_template('mail/confirm_email.html', user_id=doctor.user_id, confirm_code=code)
			body_text = render_template('mail/confirm_email.txt', user_id=doctor.user_id, confirm_code=code)

			# send_email(doctor.user.change_config['new_email'], 'Confirm your new email', body_html, body_text)

			flash('A verification link has been sent to this email')

		doctor.name = form.name.data
		doctor.gender = form.gender.data
		doctor.address = form.address.data
		doctor.city = form.city.data

		specialization_ids = form.specializations.data
		degree_ids = form.degrees.data

		doctor.specialization = [Specialization.query.get(i) for i in specialization_ids]
		doctor.degree = [Degree.query.get(i) for i in degree_ids]

		doctor.dob = form.dob.data
		doctor.contact = form.contact.data

		db.session.commit()

		flash('Records updated successfully!')

	elif request.method == 'GET':
		form.id.data = doctor.user.id
		form.email.data = doctor.user.email

		form.name.data = doctor.name
		form.gender.data = doctor.gender
		form.address.data = doctor.address
		form.city.data = doctor.city

		form.specializations.data = [i.id for i in doctor.specialization]
		form.degrees.data = [i.id for i in doctor.specialization]

		form.dob.data = doctor.dob
		form.contact.data = doctor.contact

	return render_template('receptionist/doctor_details.html', doctor=doctor, form=form)


@receptionist_app.route('/doctor/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def delete_doctor(user_id):
	user = User.query.filter_by(id=user_id).first()
	doctor = Doctor.query.filter_by(user_id=user_id).first()

	db.session.delete(doctor)
	db.session.delete(user)

	db.session.commit()

	return redirect(url_for('receptionist.list_doctor'))


@receptionist_app.route('/schedule/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def schedule(doctor_id):
	form = ScheduleForm()

	schedules = Schedule.query.filter_by(doctor_id=doctor_id).all()

	if form.validate_on_submit():
		day = form.day.data
		start_time = form.start_time.data
		end_time = form.end_time.data

		schedule = Schedule(day, start_time, end_time, doctor_id)
		schedule.save()

		return redirect(url_for('receptionist.schedule', doctor_id=doctor_id))

	return render_template('receptionist/list_schedule.html', schedules=enumerate(schedules), form=form)


@receptionist_app.route('/schedule/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def edit_schedule(schedule_id):
	form = ScheduleForm()

	schedule = Schedule.query.filter_by(id=schedule_id).first()

	if form.validate_on_submit():
		schedule.day = form.day.data
		schedule.start_time = form.start_time.data
		schedule.end_time = form.end_time.data

		db.session.commit()

		return redirect(url_for('receptionist.schedule', doctor_id=schedule.doctor_id))

	elif request.method == 'GET':
		form.day.data = schedule.day
		form.start_time.data = schedule.start_time
		form.end_time.data = schedule.end_time

	return render_template('receptionist/edit_schedule.html', schedule=schedule, form=form)


@receptionist_app.route('/schedule/<int:schedule_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def delete_schedule(schedule_id):
	schedule = Schedule.query.filter_by(id=schedule_id).first()

	db.session.delete(schedule)
	db.session.commit()

	return redirect(url_for('receptionist.schedule', doctor_id=schedule.doctor_id))


@receptionist_app.route('/appointment/add')
@login_required
@user_permission('receptionist')
def available_doctors():
	# get doctors that are present today
	doctors = db.session.query(Doctor).join(Schedule).filter(Schedule.day==day_of_week()).all()

	return render_template('receptionist/available_doctors.html', doctors=doctors)


@receptionist_app.route('/appointment/add/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def add_appointment(doctor_id):
	form = AddAppointmentForm()

	patients = db.session.query(Patient.id, Patient.name).all()
	form.patient.choices.extend(patients)

	prev_appointment = Appointment.query.filter_by(doctor_id=doctor_id, date_of_visit=datetime.today().date()).order_by(Appointment.start_time.desc()).first()

	schedule = Schedule.query.filter_by(doctor_id=doctor_id, day=day_of_week()).first()

	if form.validate_on_submit():
		date_of_visit = datetime.today().date()
		start_time = form.start_time.data
		slot = form.slot.data
		end_time = add_time(start_time, minutes=slot)
		patient_id = form.patient.data

		if end_time > schedule.end_time:
			flash("Time exceeds the Doctor's schedule!!!")

			return redirect(url_for('receptionist.add_appointment', doctor_id=doctor_id))

		new_appointment = Appointment(date_of_visit, start_time, end_time, slot, patient_id, doctor_id)
		new_appointment.save()

		return redirect(url_for('receptionist.list_appointment'))

	elif request.method == 'GET':
		form.date.data = datetime.today().strftime('%a, %d %B')
		form.doctor.data = doctor_id

		if prev_appointment:
			form.start_time.data = prev_appointment.end_time

		elif schedule:
			form.start_time.data = schedule.start_time

	return render_template('receptionist/add_appointment.html', form=form, doctor_name=schedule.doctor.name)


@receptionist_app.route('/appointment/list')
@login_required
@user_permission('receptionist')
def list_appointment():

	appointments = Appointment.query.order_by(Appointment.start_time.desc()).all()

	return render_template('receptionist/list_appointment.html', appointments=appointments)


@receptionist_app.route('/appointment/<int:appointment_id>/edit', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def edit_appointment(appointment_id):
	form = UpdateAppointmentForm()

	patients = db.session.query(Patient.id, Patient.name).all()
	form.patient.choices.extend(patients)

	appointment = Appointment.query.filter_by(id=appointment_id).first()

	# check if some appointment has been made after the current appointment
	other_appointment = Appointment.query.filter_by(doctor_id=appointment.doctor_id, date_of_visit=datetime.today().date()).order_by(Appointment.start_time.desc()).first()

	if form.validate_on_submit():
		if appointment.date_of_visit != datetime.today().date():

			flash("Cant't modify the appointment details now!!!")
			return redirect(url_for('receptionist.edit_appointment', appointment_id=appointment_id))

		appointment.patient_id = form.patient.data
		appointment.status = form.status.data

		if form.slot.data != appointment.slot:
			if appointment == other_appointment:
				appointment.slot = form.slot.data
				appointment.end_time = add_time(appointment.start_time, minutes=appointment.slot)

			else:
				form.slot.data = appointment.slot
				form.end_time.data = appointment.end_time

				flash("Can't change the slot length!!!")
				return redirect(url_for('receptionist.edit_appointment', appointment_id=appointment_id))

		db.session.commit()

		return redirect(url_for('receptionist.list_appointment'))

	elif request.method == 'GET':
		form.date.data = appointment.date_of_visit
		form.start_time.data = appointment.start_time
		form.end_time.data = appointment.end_time
		form.slot.data = appointment.slot
		form.patient.data = appointment.patient_id
		form.status.data = appointment.status
		form.doctor.data = appointment.doctor_id

	return render_template('receptionist/edit_appointment.html', form=form)


@receptionist_app.route('/appointment/<int:appointment_id>/<int:status>/status')
@login_required
@user_permission('receptionist')
def change_appointment_status(appointment_id, status):
	appointment = Appointment.query.get(appointment_id)

	appointment.status = status
	db.session.commit()

	return redirect(url_for('receptionist.list_appointment'))


@receptionist_app.route('/appointment_request')
@login_required
@user_permission('receptionist')
def appointment_request():
	appointment_requests = AppointmentRequest.query.order_by(AppointmentRequest.date.desc()).all()

	return render_template('receptionist/appointment_requests.html', appointment_requests=appointment_requests)


@receptionist_app.route('/appointment_request/add/<int:request_id>', methods=['GET', 'POST'])
@login_required
@user_permission('receptionist')
def add_appointment_request(request_id):
	form = AddAppointmentForm()

	appointment_request = AppointmentRequest.query.filter_by(id=request_id).first()

	patients = db.session.query(Patient.id, Patient.name).all()
	form.patient.choices.extend(patients)

	prev_appointment = Appointment.query.filter_by(doctor_id=appointment_request.doctor_id, date_of_visit=datetime.today().date()).order_by(Appointment.start_time.desc()).first()

	schedule = Schedule.query.filter_by(doctor_id=appointment_request.doctor_id, day=day_of_week()).first()

	if form.validate_on_submit():
		date_of_visit = datetime.today().date()
		start_time = form.start_time.data
		slot = form.slot.data
		end_time = add_time(start_time, minutes=slot)
		patient_id = form.patient.data

		if end_time > schedule.end_time:
			flash("Time exceeds the Doctor's schedule!!!")

			return redirect(url_for('receptionist.add_appointment', appointment_request.doctor_id))

		new_appointment = Appointment(date_of_visit, start_time, end_time, slot, patient_id, appointment_request.doctor_id)
		new_appointment.save()

		db.session.delete(appointment_request)
		db.session.commit()

		return redirect(url_for('receptionist.list_appointment'))

	elif request.method == 'GET':
		form.date.data = datetime.today().strftime('%a, %d %B')
		form.doctor.data = appointment_request.doctor_id
		form.patient.data = appointment_request.patient_id

		if prev_appointment:
			form.start_time.data = prev_appointment.end_time

		elif schedule:
			form.start_time.data = schedule.start_time

	return render_template('receptionist/add_appointment.html', form=form, doctor_name=schedule.doctor.name)


@receptionist_app.route('/appointment_request/reject/<int:request_id>')
@login_required
@user_permission('receptionist')
def reject_appointment_request(request_id):
	appointment_request = AppointmentRequest.query.filter_by(id=request_id).first()

	appointment_request.status = 1
	db.session.commit()

	return redirect(url_for('receptionist.appointment_request'))
