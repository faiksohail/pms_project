from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

from myproject import db, login_manager


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)


class User(db.Model, UserMixin):
	__tablename__ = 'user'

	id = db.Column(db.BigInteger, primary_key=True, index=True)
	email = db.Column(db.String(128), unique=True, nullable=False, index=True)
	password = db.Column(db.String(128), nullable=False)
	created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	modified = db.Column(db.DateTime)
	change_config = db.Column(db.PickleType)

	role = db.relationship('Role', secondary='user_roles', backref=db.backref('user', lazy='dynamic'))

	def __init__(self, email, password):
		self.email = email
		self.password = generate_password_hash(password)

	def __repr__(self):
		return f'user({self.id},{self.email},{self.created})'

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def add_role(self, role):
		self.role.append(role)

	def save(self):
		db.session.add(self)
		db.session.commit()


class Role(db.Model):
	__tablename__ = 'role'

	id = db.Column(db.Integer, primary_key=True)
	role = db.Column(db.String(20), unique=True, nullable=False)

	def __init__(self, role):
		self.role = role

	def __repr__(self):
		return f'role({self.id},{self.role})'

	@classmethod
	def get_role(cls, role):
		return cls.query.filter_by(role=role).first()


user_roles = db.Table('user_roles',
                      db.Column('user_id', db.BigInteger, db.ForeignKey('user.id')),
                      db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
                      )


class Doctor(db.Model):
	__tablename__ = 'doctor'

	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(70), nullable=False)
	gender = db.Column(db.String(8), nullable=False)
	address = db.Column(db.String(150), nullable=False)
	city = db.Column(db.String(150))
	dob = db.Column(db.DateTime)
	contact = db.Column(db.BigInteger, unique=True)
	user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)

	user = db.relationship('User', backref=db.backref('doctor', lazy='dynamic', cascade="delete"))

	specialization = db.relationship('Specialization', secondary='doctor_specializations',
										backref=db.backref('doctor', lazy='dynamic'))

	degree = db.relationship('Degree', secondary='doctor_degrees', backref=db.backref('doctor', lazy='dynamic'))

	def __init__(self, name, gender, address, city, dob, contact, user_id):
		self.name = name
		self.gender = gender
		self.address = address
		self.city = city
		self.dob = dob
		self.contact = contact
		self.user_id = user_id

	def __repr__(self):
		return f'doctor({self.id},{self.name},{self.gender},{self.address},{self.city},{self.dob},{self.contact},{self.user_id})'

	def add_specializations(self, specializations):
		self.specialization.extend(specializations)

	def add_degrees(self, degrees):
		self.degree.extend(degrees)

	def save(self):
		db.session.add(self)
		db.session.commit()


class Specialization(db.Model):
	__tablename__ = 'specialization'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(40), unique=True, nullable=False)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return f'specialization({self.id},{self.name})'

	@classmethod
	def specialization_choices(cls):
		specializations = cls.query.all()

		choices = [(row.id, row.name) for row in specializations]
		return choices


doctor_specializations = db.Table('doctor_specializations',
									db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id')),
									db.Column('specialization_id', db.Integer, db.ForeignKey('specialization.id'))
									)


class Degree(db.Model):
	__tablename__ = 'degree'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20), unique=True, nullable=False)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return f'specialist({self.id},{self.name})'

	@classmethod
	def degree_choices(cls):
		degrees = cls.query.all()

		choices = [(row.id, row.name) for row in degrees]
		return choices


doctor_degrees = db.Table('doctor_degrees',
							db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id')),
							db.Column('degree_id', db.Integer, db.ForeignKey('degree.id'))
							)


class Schedule(db.Model):
	__tablename__ = 'schedule'

	id = db.Column(db.Integer, primary_key=True, index=True)
	day = db.Column(db.String(10), nullable=False)
	start_time = db.Column(db.Time)
	end_time = db.Column(db.Time)
	doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

	doctor = db.relationship('Doctor', backref=db.backref('schedule', lazy='dynamic', cascade="all, delete"))

	def __init__(self, day, start_time, end_time, doctor_id):
		self.day = day
		self.start_time = start_time
		self.end_time = end_time
		self.doctor_id = doctor_id

	def __repr__(self):
		return f'schedule({self.id},{self.day},{self.start_time},{self.end_time})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class Appointment(db.Model):
	__tablename__ = 'appointment'

	id = db.Column(db.Integer, primary_key=True, index=True)
	date_of_visit = db.Column(db.Date, nullable=False, index=True)
	start_time = db.Column(db.Time, nullable=False)
	end_time = db.Column(db.Time, nullable=False)
	slot = db.Column(db.SmallInteger, nullable=False)
	status = db.Column(db.SmallInteger, default=0)
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
	doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)
	doc_available = db.Column(db.Boolean, default=True)

	doctor = db.relationship('Doctor', backref=db.backref('appointment', lazy='dynamic'))
	patient = db.relationship('Patient', backref=db.backref('appointment', lazy='dynamic', cascade="all, delete"))

	def __init__(self, date_of_visit, start_time, end_time, slot, patient_id, doctor_id):
		self.date_of_visit = date_of_visit
		self.start_time = start_time
		self.end_time = end_time
		self.slot = slot
		self.patient_id = patient_id
		self.doctor_id = doctor_id

	def __repr__(self):
		return f'appointment({self.id},{self.date_of_visit},{self.start_time},{self.end_time},{self.patient_id},{self.doctor_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class Receptionist(db.Model):
	__tablename__ = 'receptionist'

	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(70), nullable=False)
	gender = db.Column(db.String(8), nullable=False)
	address = db.Column(db.String(150), nullable=False)
	city = db.Column(db.String(150))
	dob = db.Column(db.DateTime)
	contact = db.Column(db.BigInteger, unique=True)
	user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)

	user = db.relationship('User', backref=db.backref('receptionist', lazy='dynamic', cascade="delete"))

	def __init__(self, name, gender, address, city, dob, contact, user_id):
		self.name = name
		self.gender = gender
		self.address = address
		self.city = city
		self.dob = dob
		self.contact = contact
		self.user_id = user_id

	def __repr__(self):
		return f'receptionist({self.id},{self.name},{self.gender},{self.address},{self.city},{self.dob},{self.contact},{self.user_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class Patient(db.Model):
	__tablename__ = 'patient'

	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(70), nullable=False)
	gender = db.Column(db.String(8), nullable=False)
	address = db.Column(db.String(150), nullable=False)
	city = db.Column(db.String(150))
	dob = db.Column(db.DateTime)
	contact = db.Column(db.BigInteger, unique=True)
	user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)

	user = db.relationship('User', backref=db.backref('patient', lazy='dynamic', cascade="delete"))

	def __init__(self, name, gender, address, city, dob, contact, user_id):
		self.name = name
		self.gender = gender
		self.address = address
		self.city = city
		self.dob = dob
		self.contact = contact
		self.user_id = user_id

	def __repr__(self):
		return f'patient({self.id},{self.name},{self.gender},{self.address},{self.city},{self.dob},{self.contact})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class PatientRecord(db.Model):
	__tablename__ = 'patient_record'

	id = db.Column(db.Integer, primary_key=True)
	symptoms = db.Column(db.Text)
	disease = db.Column(db.Text)
	description = db.Column(db.Text)
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
	appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False, unique=True)

	patient = db.relationship('Patient', backref=db.backref('patient_record', lazy='dynamic', cascade="all, delete"))
	appointment = db.relationship('Appointment', backref=db.backref('patient_record', uselist=False, cascade="delete"))

	def __init__(self, symptoms, disease, description, patient_id, appointment_id):
		self.symptoms = symptoms
		self.disease = disease
		self.description = description
		self.patient_id = patient_id
		self.appointment_id = appointment_id

	def __repr__(self):
		return f'patient_record({self.id},{self.symptoms},{self.patient_id},{self.disease},{self.description},{self.appointment_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class PatientVital(db.Model):
	__tablename__ = 'patient_vital'

	id = db.Column(db.Integer, primary_key=True)
	bp_systolic = db.Column(db.SmallInteger)
	bp_diastolic = db.Column(db.SmallInteger)
	temperature = db.Column(db.Float)
	pulse = db.Column(db.Float)
	weight = db.Column(db.Float)
	height = db.Column(db.Float)
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
	appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False, unique=True)

	patient = db.relationship('Patient', backref=db.backref('vitals', lazy='dynamic', cascade="all, delete"))
	appointment = db.relationship('Appointment', backref=db.backref('patient_vital', uselist=False, cascade="delete"))

	def __init__(self, bp_systolic, bp_diastolic, temperature, pulse, weight, height, patient_id, appointment_id):
		self.bp_systolic = bp_systolic
		self.bp_diastolic = bp_diastolic
		self.temperature = temperature
		self.pulse = pulse
		self.weight = weight
		self.height = height
		self.patient_id = patient_id
		self.appointment_id = appointment_id

	def __repr__(self):
		return f'patient_vital({self.id},{self.bp_systolic},{self.bp_diastolic},{self.temperature},{self.pulse},,{self.weight},{self.height},{self.patient_id},{self.appointment_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class PatientPrescription(db.Model):
	__tablename__ = 'patient_prescription'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), nullable=False)
	quantity = db.Column(db.String(30))
	directions = db.Column(db.String(150))
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
	appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)

	patient = db.relationship('Patient', backref=db.backref('prescription', lazy='dynamic', cascade="all, delete"))
	appointment = db.relationship('Appointment', backref=db.backref('patient_prescription', lazy='dynamic', cascade="delete"))

	def __init__(self, name, quantity, directions, patient_id, appointment_id):
		self.name = name
		self.quantity = quantity
		self.directions = directions
		self.patient_id = patient_id
		self.appointment_id = appointment_id

	def __repr__(self):
		return f'patient_prescription({self.id},{self.name},{self.patient_id},{self.quantity},{self.directions},{self.appointment_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class PatientTest(db.Model):
	__tablename__ = 'patient_test'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), nullable=False)
	details = db.Column(db.String(150))
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
	appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)

	patient = db.relationship('Patient', backref=db.backref('test', lazy='dynamic', cascade="all, delete"))
	appointment = db.relationship('Appointment', backref=db.backref('patient_test', lazy='dynamic', cascade="all, delete"))

	def __init__(self, name, details, patient_id, appointment_id):
		self.name = name
		self.details = details
		self.patient_id = patient_id
		self.appointment_id = appointment_id

	def __repr__(self):
		return f'patient_test({self.id},{self.name},{self.patient_id},{self.details},{self.appointment_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class TestReport(db.Model):
	__tablename__ = 'test_report'

	id = db.Column(db.Integer, primary_key=True)
	filename = db.Column(db.String(64), nullable=False)
	test_id = db.Column(db.Integer, db.ForeignKey('patient_test.id'), nullable=False, unique=True)

	test = db.relationship('PatientTest', backref=db.backref('report', uselist=False, cascade="delete"))

	def __init__(self, filename, test_id):
		self.filename = filename
		self.test_id = test_id

	def __repr__(self):
		return f'test_report({self.id},{self.filename},{self.test_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


class AppointmentRequest(db.Model):
	__tablename__ = 'appointment_request'

	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.Date, nullable=False, index=True)
	visit_reason = db.Column(db.String(60), nullable=False)
	status = db.Column(db.SmallInteger, default=0)
	patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
	doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

	patient = db.relationship('Patient', backref=db.backref('appointment_request', lazy='dynamic'))
	doctor = db.relationship('Doctor', backref=db.backref('appointment_request', lazy='dynamic'))

	def __init__(self, date, visit_reason, patient_id, doctor_id):
		self.date = date
		self.visit_reason = visit_reason
		self.patient_id = patient_id
		self.doctor_id = doctor_id

	def __repr__(self):
		return f'appointment({self.id},{self.date},{self.visit_reason},{self.status},{self.patient_id},{self.doctor_id})'

	def save(self):
		db.session.add(self)
		db.session.commit()


def init_db():
	if db.session.query(Specialization).count() == 0:
		s1 = Specialization('cardiologist')
		s2 = Specialization('e n t')
		s3 = Specialization('allergist')
		s4 = Specialization('psychiatrist')
		db.session.add_all([s1, s2, s3, s4])
		db.session.commit()

	if db.session.query(Degree).count() == 0:
		d1 = Degree('MBBS')
		d2 = Degree('MD')
		d3 = Degree('BMBS')
		d4 = Degree('Med')
		db.session.add_all([d1, d2, d3, d4])
		db.session.commit()

	if db.session.query(Role).count() == 0:
		r1 = Role('admin')
		r2 = Role('patient')
		r3 = Role('doctor')
		r4 = Role('receptionist')
		db.session.add_all([r1, r2, r3, r4])
		db.session.commit()

	if db.session.query(User).count() == 0:
		admin = User('admin@123.com', 'admin')
		admin.save()
		admin.add_role(Role.query.filter_by(role='admin').first())
		db.session.commit()
