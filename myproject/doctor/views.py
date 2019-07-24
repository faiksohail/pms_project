from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import uuid

from myproject import db
from myproject.models import User, Doctor, Degree, Specialization, Patient, Appointment, PatientRecord, PatientVital, PatientPrescription, PatientTest
from myproject.forms import LoginForm, UpdateDoctorForm, ChangePasswordForm
from myproject.doctor.forms import MedicalRecordForm, VitalsForm, PrescriptionForm, TestOrderForm, SearchForm
from myproject.utilities.permission import user_permission

doctor_app = Blueprint('doctor', __name__, template_folder='templates')


@doctor_app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if current_user.is_authenticated:
		return redirect(url_for('doctor.index'))

	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()

		if user is not None and user.check_password(form.password.data):
			login_user(user, remember=form.remember_me.data)

			next = request.args.get('next')
			if next is None or next[0] != '/':
				next = url_for('doctor.index')

			return redirect(next)

		flash('Incorrect username or password')
		return render_template('doctor/login.html', form=form)

	return render_template('doctor/login.html', form=form)


@doctor_app.route('/logout')
@login_required
@user_permission('doctor')
def logout():

	logout_user()

	return redirect(url_for('doctor.login'))


@doctor_app.route('/account', methods=['GET', 'POST'])
@login_required
@user_permission('doctor')
def account():
	form = UpdateDoctorForm()

	user = Doctor.query.filter_by(user_id=current_user.id).first()

	form.specializations.choices = Specialization.specialization_choices()
	form.degrees.choices = Degree.degree_choices()

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

		specialization_ids = form.specializations.data
		degree_ids = form.degrees.data

		user.specialization = [Specialization.query.get(i) for i in specialization_ids]
		user.degree = [Degree.query.get(i) for i in degree_ids]

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

		form.specializations.data = [i.id for i in user.specialization]
		form.degrees.data = [i.id for i in user.specialization]

		form.dob.data = user.dob
		form.contact.data = user.contact

	return render_template('doctor/account.html', form=form, name=user.name)


@doctor_app.route('/change_password', methods=['GET', 'POST'])
@login_required
@user_permission('doctor')
def change_password():
	form = ChangePasswordForm()

	user = Doctor.query.filter_by(user_id=current_user.id).first()

	if form.validate_on_submit():
		if current_user.check_password(form.current_pwd.data):
			if form.current_pwd.data != form.new_password.data:
				current_user.set_password(form.new_password.data)

				db.session.commit()

				return redirect(url_for('doctor.index'))
			else:
				flash('You must use a new password!')
		else:
			flash('Incorrect password!')

	return render_template('doctor/change_password.html', form=form, name=user.name)


@doctor_app.route('/')
@doctor_app.route('/index')
@login_required
@user_permission('doctor')
def index():
	doctor = Doctor.query.filter_by(user_id=current_user.id).first()

	# get todays appointments
	appointments = Appointment.query.filter_by(doctor_id=doctor.id, date_of_visit=datetime.today().date()).order_by(Appointment.start_time.desc()).all()

	return render_template('doctor/index.html', appointments=appointments)


@doctor_app.route('/appointments/recent')
@login_required
@user_permission('doctor')
def recent_appointments():

	doctor = Doctor.query.filter_by(user_id=current_user.id).first()

	appointments = Appointment.query.filter_by(doctor_id=doctor.id, date_of_visit=datetime.today().date()).order_by(Appointment.start_time.desc()).all()

	return render_template('doctor/appointments.html', appointments=appointments)


@doctor_app.route('/appointments')
@login_required
@user_permission('doctor')
def appointments():

	doctor = Doctor.query.filter_by(user_id=current_user.id).first()

	appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.start_time.desc()).all()

	return render_template('doctor/appointments.html', appointments=appointments)


@doctor_app.route('/appointment/<int:appointment_id>/<int:status>/status')
@login_required
@user_permission('doctor')
def change_appointment_status(appointment_id, status):
	appointment = Appointment.query.get(appointment_id)

	appointment.status = status
	db.session.commit()

	return redirect(url_for('doctor.appointments'))


@doctor_app.route('/patient/<int:patient_id>/<int:appointment_id>')
@login_required
@user_permission('doctor')
def patient_details(patient_id, appointment_id):

	doctor = Doctor.query.filter_by(user_id=current_user.id).first()

	patient = Patient.query.filter_by(id=patient_id).first()

	current_appointment = Appointment.query.get(appointment_id)

	prev_appointments = Appointment.query.filter_by(patient_id=patient_id, doctor_id=doctor.id, status=1).order_by(Appointment.date_of_visit.desc()).all()

	return render_template('doctor/patient_details.html', patient=patient, prev_appointments=prev_appointments, current_appointment=current_appointment)


@doctor_app.route('/patient/<int:patient_id>/<int:appointment_id>/add', methods=['GET', 'POST'])
@login_required
@user_permission('doctor')
def add_record(patient_id, appointment_id):
	form1 = MedicalRecordForm(prefix='form1')
	form2 = VitalsForm(prefix='form2')
	form3 = PrescriptionForm(prefix='form3')
	form4 = PrescriptionForm()
	form5 = TestOrderForm(prefix='form5')
	form6 = TestOrderForm()

	patient = Patient.query.filter_by(id=patient_id).first()

	current_appointment = Appointment.query.get(appointment_id)

	patient_record = PatientRecord.query.filter_by(appointment_id=appointment_id).first()

	patient_vital = PatientVital.query.filter_by(appointment_id=appointment_id).first()

	patient_prescription = PatientPrescription.query.filter_by(appointment_id=appointment_id, patient_id=patient_id).all()

	patient_test = PatientTest.query.filter_by(appointment_id=appointment_id, patient_id=patient_id).all()

	if request.method == 'POST':
		if form1.submit.data and form1.validate_on_submit():
			if patient_record:
				patient_record.symptoms = form1.symptoms.data
				patient_record.disease = form1.disease.data
				patient_record.description = form1.description.data

				db.session.commit()

				return redirect(url_for('doctor.add_record', patient_id=patient_id, appointment_id=appointment_id))

			else:
				record = PatientRecord(form1.symptoms.data, form1.disease.data, form1.description.data, patient_id, appointment_id)
				record.save()

				current_appointment.status = 1
				db.session.commit()

				return redirect(url_for('doctor.add_record', patient_id=patient_id, appointment_id=appointment_id))

		if form2.submit.data and form2.validate_on_submit():
			if patient_vital:
				patient_vital.bp_systolic = form2.bp_systolic.data
				patient_vital.bp_diastolic = form2.bp_diastolic.data
				patient_vital.temperature = form2.temperature.data
				patient_vital.pulse = form2.pulse.data
				patient_vital.weight = form2.weight.data
				patient_vital.height = form2.height.data

				db.session.commit()

				return redirect(url_for('doctor.add_record', patient_id=patient_id, appointment_id=appointment_id))

			else:
				vital = PatientVital(form2.bp_systolic.data, form2.bp_diastolic.data, form2.temperature.data,
				                     form2.pulse.data, form2.weight.data, form2.height.data, patient_id, appointment_id)
				vital.save()

				current_appointment.status = 1
				db.session.commit()

				return redirect(url_for('doctor.add_record', patient_id=patient_id, appointment_id=appointment_id))

		if form3.submit.data and form3.validate_on_submit():

			prescription = PatientPrescription(form3.name.data, form3.quantity.data, form3.directions.data, patient_id, appointment_id)
			prescription.save()

			current_appointment.status = 1
			db.session.commit()

			return redirect(url_for('doctor.add_record', patient_id=patient_id, appointment_id=appointment_id))

		if form5.submit.data and form5.validate_on_submit():

			test = PatientTest(form5.test_name.data, form5.test_details.data, patient_id, appointment_id)
			test.save()

			current_appointment.status = 1
			db.session.commit()

			return redirect(url_for('doctor.add_record', patient_id=patient_id, appointment_id=appointment_id))

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

	return render_template('doctor/add_record.html', today=datetime.today().date(), patient=patient, current_appointment=current_appointment, patient_prescription=patient_prescription, patient_test=patient_test,
	                       form1=form1, form2=form2, form3=form3, form4=form4, form5=form5, form6=form6)


@doctor_app.route('/patient/<int:prescription_id>/prescription_update', methods=['POST'])
@login_required
@user_permission('doctor')
def update_prescription(prescription_id):
	form = PrescriptionForm()

	prescription = PatientPrescription.query.get(prescription_id)

	if form.validate_on_submit():

		prescription.name = form.name.data
		prescription.quantity = form.quantity.data
		prescription.directions = form.directions.data

		db.session.commit()

	return redirect(url_for('doctor.add_record', patient_id=prescription.patient_id, appointment_id=prescription.appointment_id))


@doctor_app.route('/patient/<int:prescription_id>/prescription_delete', methods=['POST'])
@login_required
@user_permission('doctor')
def delete_prescription(prescription_id):
	prescription = PatientPrescription.query.get(prescription_id)

	db.session.delete(prescription)

	db.session.commit()

	return redirect(url_for('doctor.add_record', patient_id=prescription.patient_id, appointment_id=prescription.appointment_id))


@doctor_app.route('/patient/<int:test_id>/test_update', methods=['POST'])
@login_required
@user_permission('doctor')
def update_test(test_id):
	form = TestOrderForm()

	test = PatientTest.query.get(test_id)

	if form.validate_on_submit():

		test.name = form.test_name.data
		test.details = form.test_details.data

		db.session.commit()

	return redirect(url_for('doctor.add_record', patient_id=test.patient_id, appointment_id=test.appointment_id))


@doctor_app.route('/patient/<int:test_id>/test_delete', methods=['POST'])
@login_required
@user_permission('doctor')
def delete_test(test_id):
	test = PatientTest.query.get(test_id)

	db.session.delete(test)

	db.session.commit()

	return redirect(url_for('doctor.add_record', patient_id=test.patient_id, appointment_id=test.appointment_id))


@doctor_app.route('/patient/<int:appointment_id>/list', methods=['GET', 'POST'])
@login_required
@user_permission('doctor')
def list_records(appointment_id):

	record = PatientRecord.query.filter_by(appointment_id=appointment_id).first()

	vital = PatientVital.query.filter_by(appointment_id=appointment_id).first()

	prescription = PatientPrescription.query.filter_by(appointment_id=appointment_id).all()

	test = PatientTest.query.filter_by(appointment_id=appointment_id).all()

	return render_template('doctor/list_record.html', record=record, vital=vital, prescription=prescription, test=test)


@doctor_app.route('/patient/search', methods=['GET', 'POST'])
@login_required
@user_permission('doctor')
def search_patient():
	form = SearchForm()

	search_result=0

	if form.validate_on_submit():
		filter = form.filter.data

		if filter == '1':
			search_result = Patient.query.filter_by(user_id=form.search.data).all()

		elif filter == '2':
			search_result = db.session.query(Patient).join(User).filter(User.email==form.search.data).all()

		elif filter == '3':
			search_result = Patient.query.filter(Patient.name.contains(form.search.data)).all()

		return render_template('doctor/search_patient.html', form=form, search_result=search_result)

	return render_template('doctor/search_patient.html', form=form, search_result=search_result)


@doctor_app.route('/patient/search/<int:patient_id>')
@login_required
@user_permission('doctor')
def show_patient(patient_id):

	patient = Patient.query.filter_by(id=patient_id).first()

	appointments = Appointment.query.filter_by(patient_id=patient_id, status=1).order_by(Appointment.date_of_visit.desc()).all()

	return render_template('doctor/show_patient.html', patient=patient, appointments=appointments)


@doctor_app.route('/patient/<int:appointment_id>/show', methods=['GET', 'POST'])
@login_required
@user_permission('doctor')
def show_patient_records(appointment_id):

	record = PatientRecord.query.filter_by(appointment_id=appointment_id).first()

	vital = PatientVital.query.filter_by(appointment_id=appointment_id).first()

	prescription = PatientPrescription.query.filter_by(appointment_id=appointment_id).all()

	test = PatientTest.query.filter_by(appointment_id=appointment_id).all()

	return render_template('doctor/show_patient_records.html', record=record, vital=vital, prescription=prescription, test=test)

