from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import uuid

from myproject import db
from myproject.models import Patient, Doctor, Schedule,Receptionist, User, Role, Specialization, Degree, Appointment, PatientRecord, PatientVital, PatientTest, PatientPrescription, AppointmentRequest
from myproject.forms import LoginForm, AddForm, UpdateForm, AddDoctorForm, UpdateDoctorForm, ChangePasswordForm
from myproject.admin.forms import AccountForm, AddSpecializationForm, AddDegreeForm, AddRoleForm
from myproject.receptionist.forms import UpdateAppointmentForm, ScheduleForm
from myproject.doctor.forms import MedicalRecordForm, PrescriptionForm, VitalsForm, TestOrderForm
from myproject.utilities.permission import user_permission
from myproject.utilities.password_generator import generate_random_password
from myproject.utilities.mail_sender import send_email
from myproject.utilities.time_functions import add_time

admin_app = Blueprint('admin', __name__, template_folder='templates')


@admin_app.route('/', methods=['GET', 'POST'])
@admin_app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if current_user.is_authenticated:
		return redirect(url_for('admin.index'))

	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		admin = Role.query.filter_by(role='admin').first()

		if user is not None and user.check_password(form.password.data) and admin in user.role:
			login_user(user, remember=form.remember_me.data)

			next = request.args.get('next')
			if next is None or next[0] != '/':
				next = url_for('admin.index')

			return redirect(next)

		flash('Incorrect username or password')
		return render_template('admin/login.html', form=form)

	return render_template('admin/login.html', form=form)


@admin_app.route('/logout')
@login_required
@user_permission('admin')
def logout():

	logout_user()

	return redirect(url_for('admin.login'))


@admin_app.route('/account', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def account():
	form = AccountForm()

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

		db.session.commit()

	elif request.method == 'GET':
		form.id.data = current_user.id
		form.email.data = current_user.email

	return render_template('admin/account.html', form=form)


@admin_app.route('/change_password', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def change_password():
	form = ChangePasswordForm()

	if form.validate_on_submit():
		if current_user.check_password(form.current_pwd.data):
			if form.current_pwd.data != form.new_password.data:
				current_user.set_password(form.new_password.data)

				db.session.commit()

				return redirect(url_for('admin.index'))
			else:
				flash('You must use a new password!')
		else:
			flash('Incorrect password!')

	return render_template('admin/change_password.html', form=form)


@admin_app.route('/index')
@login_required
@user_permission('admin')
def index():
	patient_count = Patient.query.count()

	doctor_count = Doctor.query.count()

	receptionist_count = Receptionist.query.count()

	appointment_count = Appointment.query.filter_by(date_of_visit=datetime.today().date()).count()

	return render_template('admin/index.html', patient_count=patient_count, doctor_count=doctor_count, receptionist_count=receptionist_count, appointment_count=appointment_count)


@admin_app.route('/users')
@login_required
@user_permission('admin')
def users():
	admin_role = Role.query.filter_by(role='admin').first()

	users = User.query.filter(~User.role.contains(admin_role)).order_by(User.id).all()

	return render_template('admin/users.html', users=users)


@admin_app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def add_role(user_id):
	form = AddRoleForm()
	user = User.query.filter_by(id=user_id).first()

	roles = Role.query.filter(Role.role != 'admin').all()

	role_choices = [(role.id, role.role) for role in roles if role not in user.role]

	form.role.choices = [(0, 'Choose an Option')]
	form.role.choices.extend(role_choices)

	for user_role in user.role:
		if 'patient' in user_role.role:
			person = Patient.query.filter_by(user_id=user.id).first()

		elif 'doctor' in user_role.role:
			person = Doctor.query.filter_by(user_id=user.id).first()

		elif 'receptionist' in user_role.role:
			person = Receptionist.query.filter_by(user_id=user.id).first()

	if form.validate_on_submit():

		new_role = Role.query.filter_by(id=form.role.data).first()

		user.add_role(new_role)
		if new_role.role == 'patient':
			patient = Patient(person.name, person.gender, person.address, person.city, person.dob, person.contact, user_id)
			patient.save()

		elif new_role.role == 'doctor':
			doctor = Doctor(person.name, person.gender, person.address, person.city, person.dob, person.contact, user_id)
			doctor.save()

		elif new_role.role == 'receptionist':
			receptionist = Receptionist(person.name, person.gender, person.address, person.city, person.dob, person.contact, user_id)
			receptionist.save()

		return redirect(url_for('admin.add_role', user_id=user_id))

	return render_template('admin/add_role.html', form=form, user=user, person=person, role_count=len(user.role))


@admin_app.route('/user/<int:user_id>/<int:role_id>/role', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_role(user_id, role_id):
	user = User.query.filter_by(id=user_id).first()

	user_role = Role.query.filter_by(id=role_id).first()

	if user_role.role == 'patient':
		person = Patient.query.filter_by(user_id=user_id).first()

	elif user_role.role == 'doctor':
		person = Doctor.query.filter_by(user_id=user_id).first()

	elif user_role.role == 'receptionist':
		person = Receptionist.query.filter_by(user_id=user_id).first()

	user.role.remove(user_role)

	db.session.delete(person)
	db.session.commit()

	return redirect(url_for('admin.add_role', user_id=user_id))


#### Patient ####
@admin_app.route('/patient/add', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
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

		body_html = render_template('mail/credentials.html', username=name, login_id=user_id, password=password)
		body_text = render_template('mail/credentials.txt', username=name, login_id=user_id, password=password)

		# send_email(email, 'Welcome to PMS', body_html, body_text)

		return redirect(url_for('admin.list_patient'))

	return render_template('admin/add_patient.html', form=form)


@admin_app.route('/patient/list')
@login_required
@user_permission('admin')
def list_patient():
	patients = Patient.query.order_by(Patient.user_id.desc()).all()

	return render_template('admin/list_patient.html', patients=patients)


@admin_app.route('/patient/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def patient_details(user_id):
	form = UpdateForm()

	patient = Patient.query.filter_by(user_id=user_id).first()

	appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date_of_visit.desc()).all()
	message = None

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

	return render_template('admin/patient_details.html', patient=patient, appointments=appointments, form=form, message=message)


@admin_app.route('/patient/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_patient(user_id):
	user = User.query.filter_by(id=user_id).first()
	patient = Patient.query.filter_by(user_id=user_id).first()

	db.session.delete(patient)
	db.session.delete(user)

	db.session.commit()

	return redirect(url_for('admin.list_patient'))


##### Doctor ####
@admin_app.route('/doctor/add', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
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

		return redirect(url_for('admin.list_doctor'))

	return render_template('admin/add_doctor.html', form=form)


@admin_app.route('/doctor/list')
@login_required
@user_permission('admin')
def list_doctor():
	doctors = Doctor.query.order_by(Doctor.user_id.desc()).all()

	return render_template('admin/list_doctor.html', doctors=doctors)


@admin_app.route('/doctor/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
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

	return render_template('admin/doctor_details.html', doctor=doctor, form=form)


@admin_app.route('/doctor/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_doctor(user_id):
	user = User.query.filter_by(id=user_id).first()
	doctor = Doctor.query.filter_by(user_id=user_id).first()

	db.session.delete(doctor)
	db.session.delete(user)

	db.session.commit()

	return redirect(url_for('admin.list_doctor'))


@admin_app.route('/schedule/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def schedule(doctor_id):
	form = ScheduleForm()

	schedules = Schedule.query.filter_by(doctor_id=doctor_id).all()

	if form.validate_on_submit():
		day = form.day.data
		start_time = form.start_time.data
		end_time = form.end_time.data

		schedule = Schedule(day, start_time, end_time, doctor_id)
		schedule.save()

		return redirect(url_for('admin.schedule', doctor_id=doctor_id))

	return render_template('admin/list_schedule.html', schedules=enumerate(schedules), form=form)


@admin_app.route('/schedule/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def edit_schedule(schedule_id):
	form = ScheduleForm()

	schedule = Schedule.query.filter_by(id=schedule_id).first()

	if form.validate_on_submit():
		schedule.day = form.day.data
		schedule.start_time = form.start_time.data
		schedule.end_time = form.end_time.data

		db.session.commit()

		return redirect(url_for('admin.schedule', doctor_id=schedule.doctor_id))

	elif request.method == 'GET':
		form.day.data = schedule.day
		form.start_time.data = schedule.start_time
		form.end_time.data = schedule.end_time

	return render_template('admin/edit_schedule.html', schedule=schedule, form=form)


@admin_app.route('/schedule/<int:schedule_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_schedule(schedule_id):
	schedule = Schedule.query.filter_by(id=schedule_id).first()

	db.session.delete(schedule)
	db.session.commit()

	return redirect(url_for('admin.schedule', doctor_id=schedule.doctor_id))


#### Receptionist ####
@admin_app.route('/receptionist/add', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def add_receptionist():
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
		receptionist_role = Role.get_role('receptionist')

		user.save()
		user.add_role(receptionist_role)

		user_id = user.id
		receptionist = Receptionist(name, gender, address, city, dob, contact, user_id)
		receptionist.save()

		body_html = render_template('mail/staff_credentials.html', email=email, password=password)
		body_text = render_template('mail/staff_credentials.txt', email=email, password=password)

		# send_email(email, 'Welcome to PMS', body_html, body_text)

		return redirect(url_for('admin.list_receptionist'))

	return render_template('admin/add_receptionist.html', form=form)


@admin_app.route('/receptionist/list')
@login_required
@user_permission('admin')
def list_receptionist():
	receptionists = Receptionist.query.order_by(Receptionist.user_id.desc()).all()

	return render_template('admin/list_receptionist.html', receptionists=receptionists)


@admin_app.route('/receptionist/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def receptionist_details(user_id):
	form = UpdateForm()

	receptionist = Receptionist.query.filter_by(user_id=user_id).first()

	if receptionist is None:
		flash('Invalid Path!!!')
		abort(404)

	if form.validate_on_submit():
		if receptionist.user.email != form.email.data:
			code = str(uuid.uuid4())
			receptionist.user.change_config = {
				'new_email': form.email.data,
				'confirm_code': code
			}

			form.email.data = receptionist.user.email

			body_html = render_template('mail/confirm_email.html', user_id=receptionist.user_id, confirm_code=code)
			body_text = render_template('mail/confirm_email.txt', user_id=receptionist.user_id, confirm_code=code)

			# send_email(receptionist.user.change_config['new_email'], 'Confirm your new email', body_html, body_text)

			flash('A verification link has been sent to this email')

		receptionist.name = form.name.data
		receptionist.gender = form.gender.data
		receptionist.address = form.address.data
		receptionist.city = form.city.data
		receptionist.dob = form.dob.data
		receptionist.contact = form.contact.data

		db.session.commit()

		flash('Records updated successfully!')

	elif request.method == 'GET':
		form.id.data = receptionist.user.id
		form.email.data = receptionist.user.email

		form.name.data = receptionist.name
		form.gender.data = receptionist.gender
		form.address.data = receptionist.address
		form.city.data = receptionist.city
		form.dob.data = receptionist.dob
		form.contact.data = receptionist.contact

	return render_template('admin/receptionist_details.html', receptionist=receptionist, form=form)


@admin_app.route('/receptionist/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_receptionist(user_id):
	user = User.query.filter_by(id=user_id).first()
	receptionist = Receptionist.query.filter_by(user_id=user_id).first()

	db.session.delete(receptionist)
	db.session.delete(user)

	db.session.commit()

	return redirect(url_for('admin.list_receptionist'))


@admin_app.route('/appointment/list')
@login_required
@user_permission('admin')
def list_appointment():

	appointments = Appointment.query.order_by(Appointment.start_time.desc()).all()

	return render_template('admin/list_appointment.html', appointments=appointments)


@admin_app.route('/appointment/<int:appointment_id>/edit', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
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
			return redirect(url_for('admin.edit_appointment', appointment_id=appointment_id))

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
				return redirect(url_for('admin.edit_appointment', appointment_id=appointment_id))

		db.session.commit()

		return redirect(url_for('admin.list_appointment'))

	elif request.method == 'GET':
		form.date.data = appointment.date_of_visit
		form.start_time.data = appointment.start_time
		form.end_time.data = appointment.end_time
		form.slot.data = appointment.slot
		form.patient.data = appointment.patient_id
		form.status.data = appointment.status
		form.doctor.data = appointment.doctor_id

	return render_template('admin/edit_appointment.html', appointment=appointment, form=form)


@admin_app.route('/appointment/<int:patient_id>')
@login_required
@user_permission('admin')
def patient_appointments(patient_id):

	appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.start_time.desc()).all()

	return render_template('admin/patient_appointments.html', appointments=appointments)


@admin_app.route('/appointment/<int:appointment_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_appointment(appointment_id):
	appointment = Appointment.query.filter_by(id=appointment_id).first()

	db.session.delete(appointment)

	db.session.commit()

	return redirect(url_for('admin.list_appointment'))


@admin_app.route('/patient/<int:patient_id>/<int:appointment_id>/record', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def patient_records(patient_id, appointment_id):

	record = PatientRecord.query.filter_by(patient_id=patient_id, appointment_id=appointment_id).first()

	vital = PatientVital.query.filter_by(patient_id=patient_id, appointment_id=appointment_id).first()

	prescription = PatientPrescription.query.filter_by(patient_id=patient_id, appointment_id=appointment_id).all()

	test = PatientTest.query.filter_by(patient_id=patient_id, appointment_id=appointment_id).all()

	return render_template('admin/patient_records.html', record=record, vital=vital, prescription=prescription, test=test)


@admin_app.route('/specialization/add', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def add_specialization():
	form = AddSpecializationForm()

	specializations = Specialization.query.all()

	if form.validate_on_submit():
		new_sp = Specialization(form.new_specialization.data)
		db.session.add(new_sp)
		db.session.commit()

		flash('Specialization added successfully.')
		return redirect(url_for('admin.add_specialization'))

	return render_template('admin/specialization.html', form=form, specializations=specializations)


@admin_app.route('/specialization/<int:sp_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_specialization(sp_id):
	specialization = Specialization.query.filter_by(id=sp_id).first()

	db.session.delete(specialization)
	db.session.commit()

	return redirect(url_for('admin.add_specialization'))


@admin_app.route('/specialists/<int:sp_id>')
@login_required
@user_permission('admin')
def specialists(sp_id):
	specialization = Specialization.query.filter_by(id=sp_id).first()

	return render_template('admin/list_specialists.html', specialization=specialization)


@admin_app.route('/degree/add', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def add_degree():
	form = AddDegreeForm()

	degrees = Degree.query.all()

	if form.validate_on_submit():
		new_dg = Degree(form.new_degree.data)
		db.session.add(new_dg)
		db.session.commit()

		flash('Degree added successfully.')
		return redirect(url_for('admin.add_degree'))

	return render_template('admin/degree.html', form=form, degrees=degrees)


@admin_app.route('/degrees/<int:dg_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_degree(dg_id):
	degree = Degree.query.filter_by(id=dg_id).first()

	db.session.delete(degree)
	db.session.commit()

	return redirect(url_for('admin.add_degree'))


@admin_app.route('/patient/<int:appointment_id>/add', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def edit_record(appointment_id):
	form1 = MedicalRecordForm(prefix='form1')
	form2 = VitalsForm(prefix='form2')
	form3 = PrescriptionForm()
	form4 = TestOrderForm()

	current_appointment = Appointment.query.get(appointment_id)

	patient_record = PatientRecord.query.filter_by(appointment_id=appointment_id).first()

	patient_vital = PatientVital.query.filter_by(appointment_id=appointment_id).first()

	patient_prescription = PatientPrescription.query.filter_by(appointment_id=appointment_id).all()

	patient_test = PatientTest.query.filter_by(appointment_id=appointment_id).all()

	if request.method == 'POST':
		if form1.submit.data and form1.validate_on_submit():
				patient_record.symptoms = form1.symptoms.data
				patient_record.disease = form1.disease.data
				patient_record.description = form1.description.data

				db.session.commit()

				return redirect(url_for('admin.edit_record', appointment_id=appointment_id))

		if form2.submit.data and form2.validate_on_submit():
			if patient_vital:
				patient_vital.bp_systolic = form2.bp_systolic.data
				patient_vital.bp_diastolic = form2.bp_diastolic.data
				patient_vital.temperature = form2.temperature.data
				patient_vital.pulse = form2.pulse.data
				patient_vital.weight = form2.weight.data
				patient_vital.height = form2.height.data

				db.session.commit()

				return redirect(url_for('admin.edit_record', appointment_id=appointment_id))

	elif request.method == 'GET':
		if patient_record:
			form1.symptoms.data = patient_record.symptoms
			form1.disease.data = patient_record.disease
			form1.description.data = patient_record.description

		if patient_vital:
			form2.bp_systolic.data = patient_vital.bp_systolic
			form2.bp_diastolic.data = patient_vital.bp_diastolic
			form2.temperature.data = patient_vital.temperature
			form2.pulse.data = patient_vital.pulse
			form2.weight.data = patient_vital.weight
			form2.height.data = patient_vital.height

	return render_template('admin/edit_record.html', today=datetime.today().date(), current_appointment=current_appointment, patient_prescription=patient_prescription, patient_test=patient_test,
	                       form1=form1, form2=form2, form3=form3, form4=form4)


@admin_app.route('/patient/<int:prescription_id>/prescription_update', methods=['POST'])
@login_required
@user_permission('admin')
def update_prescription(prescription_id):
	form = PrescriptionForm()

	prescription = PatientPrescription.query.get(prescription_id)

	if form.validate_on_submit():

		prescription.name = form.name.data
		prescription.quantity = form.quantity.data
		prescription.directions = form.directions.data

		db.session.commit()

	return redirect(url_for('admin.edit_record', appointment_id=prescription.appointment_id))


@admin_app.route('/patient/<int:prescription_id>/prescription_delete', methods=['POST'])
@login_required
@user_permission('admin')
def delete_prescription(prescription_id):
	prescription = PatientPrescription.query.get(prescription_id)

	db.session.delete(prescription)

	db.session.commit()

	return redirect(url_for('admin.edit_record', appointment_id=prescription.appointment_id))


@admin_app.route('/patient/<int:test_id>/test_update', methods=['POST'])
@login_required
@user_permission('admin')
def update_test(test_id):
	form = TestOrderForm()

	test = PatientTest.query.get(test_id)

	if form.validate_on_submit():

		test.name = form.test_name.data
		test.details = form.test_details.data

		db.session.commit()

	return redirect(url_for('admin.edit_record', appointment_id=test.appointment_id))


@admin_app.route('/patient/<int:test_id>/test_delete', methods=['POST'])
@login_required
@user_permission('admin')
def delete_test(test_id):
	test = PatientTest.query.get(test_id)

	db.session.delete(test)

	db.session.commit()

	return redirect(url_for('admin.edit_record',  appointment_id=test.appointment_id))


@admin_app.route('/appointment_request')
@login_required
@user_permission('admin')
def appointment_request():
	appointment_requests = AppointmentRequest.query.order_by(AppointmentRequest.date.desc()).all()

	return render_template('admin/appointment_requests.html', appointment_requests=appointment_requests)


@admin_app.route('/appointment_request/<int:request_id>/delete', methods=['GET', 'POST'])
@login_required
@user_permission('admin')
def delete_appointment_request(request_id):
	request = AppointmentRequest.query.filter_by(id=request_id).first();

	db.session.delete(request)

	db.session.commit()

	return redirect(url_for('admin.appointment_request'))



