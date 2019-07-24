import random, string
from faker import Faker
from datetime import datetime, timedelta
from myproject.models import *

fake_gen = Faker()

gender = ['male', 'female']
days = ['monday' , 'tuesday', 'wednesday',  'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def populate_patient(N=10):

	patient_role = Role.get_role('patient')

	for entry in range(N):

		email = fake_gen.email()
		pwd = fake_gen.text()

		number = ''.join(random.choices(string.digits, k=10))

		if not User.query.filter_by(email=email).first():
			u = User(email, pwd)
			u.save()
			u.add_role(patient_role)

			patient = Patient(fake_gen.name(), random.choice(gender), fake_gen.address(), fake_gen.city(), fake_gen.date(), number, u.id)
			patient.save()


def populate_doctor(N=10):

	doctor_role = Role.get_role('doctor')

	for entry in range(N):

		email = fake_gen.email()
		pwd = fake_gen.text()

		number = ''.join(random.choices(string.digits, k=10))

		if not User.query.filter_by(email=email).first():
			u = User(email, pwd)
			u.save()
			u.add_role(doctor_role)

			doctor = Doctor(fake_gen.name(), random.choice(gender), fake_gen.address(), fake_gen.city(), fake_gen.date(), number, u.id)

			sp_choices = random.choices(Specialization.query.all())
			dg_choices = random.choices(Degree.query.all())

			doctor.add_specializations(sp_choices)
			doctor.add_degrees(dg_choices)

			doctor.save()


def populate_receptionist(N=10):

	receptionist_role = Role.get_role('receptionist')

	for entry in range(N):

		email = fake_gen.email()
		pwd = fake_gen.text()

		number = ''.join(random.choices(string.digits, k=10))

		if not User.query.filter_by(email=email).first():
			u = User(email, pwd)
			u.save()
			u.add_role(receptionist_role)

			receptionist = Receptionist(fake_gen.name(), random.choice(gender), fake_gen.address(), fake_gen.city(), fake_gen.date(), number, u.id)
			receptionist.save()


def populate_schedule(N=20):

	for entry in range(N):

		doctor = Doctor.query.all()

		s_time = datetime.strptime(fake_gen.time(), '%H:%M:%S')
		e_time = s_time + timedelta(hours=2)
		random.choice(doctor)
		schedule = Schedule(random.choice(days), s_time, e_time, random.choice(doctor).id)
		schedule.save()


if __name__ == '__main__':
	print('Populating patient...')
	populate_patient(0)
	print('Populated patient!')

	print('Populating doctor...')
	populate_doctor(0)
	print('Populated doctor!')

	print('Populating receptionist...')
	populate_receptionist(0)
	print('Populated receptionist!')

	print('Populating schedule...')
	populate_schedule()
	print('Populated schedule!')

