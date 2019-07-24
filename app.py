import uuid, click, re
from flask import render_template, flash, request, redirect, url_for, abort
from flask_login import current_user
from datetime import datetime

from myproject import app
from myproject import db
from myproject.models import User, Role, Patient
from myproject.forms import ResetPasswordForm, ForgotPasswordForm, AddForm
from myproject.utilities.password_generator import generate_random_password
from myproject.utilities.mail_sender import send_email


@app.route('/')
@app.route('/index')
def index():
	if current_user.is_authenticated:
		admin = Role.query.filter_by(role='admin').first()
		doctor = Role.query.filter_by(role='doctor').first()
		patient = Role.query.filter_by(role='patient').first()
		receptionist = Role.query.filter_by(role='receptionist').first()

		if doctor in current_user.role:
			return redirect(url_for('doctor.index'))

		elif receptionist in current_user.role:
			return redirect(url_for('receptionist.index'))

		elif admin in current_user.role:
			return redirect(url_for('admin.index'))

		elif patient in current_user.role:
			return redirect(url_for('patient.index'))

	return render_template('first_page.html')


@app.route('/confirm/<int:user_id>/<code>')
def confirm(user_id, code):
	user = User.query.filter_by(id=user_id).first()

	if user and user.change_config and user.change_config.get('confirm_code'):
		if code == user.change_config.get('confirm_code'):
			user.email = user.change_config.get('new_email')
			user.change_config = None
			user.modified = datetime.utcnow()
			db.session.commit()
			flash('Email Confirmed')
			return render_template('confirm.html')
	else:
		abort(404)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
	form = ForgotPasswordForm()

	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()

		if user:
			code = str(uuid.uuid4())
			user.change_config = {
				'password_reset_link': code
			}
			db.session.commit()

			body_html = render_template('mail/reset_password.html', user_id=user.id, confirm_code=code)
			body_text = render_template('mail/reset_password.txt', user_id=user.id, confirm_code=code)

			# send_email(user.email, 'Password reset request', body_html, body_text)

			flash('A reset password link has been sent to this email, please check your email.')
			return redirect(url_for('forgot_password'))

		flash('Email address not recognized')

	return render_template('forgot_password.html', form=form)


@app.route('/password_reset/<int:user_id>/<code>', methods=['GET', 'POST'])
def reset_password(user_id, code):
	form = ResetPasswordForm()

	user = User.query.filter_by(id=user_id).first()

	if not user or code != user.change_config.get('password_reset_link'):
		abort(404)

	if request.method == 'POST':
		if form.validate_on_submit():
			user.set_password(form.new_password.data)
			user.change_config = None

			db.session.commit()

			return redirect(url_for('password_reset_complete'))

	return render_template('password_reset.html', form=form)


@app.route('/password_reset/complete')
def password_reset_complete():

	return render_template('password_reset_complete.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
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
		flash("Please check your email for user id and password.")

		return redirect(url_for('register'))

	return render_template('register.html', form=form)


@app.cli.command('create_superuser')
def create_superuser():
	while True:
		email = click.prompt('Enter email')
		match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)

		if not match:
			click.echo('The email is not valid. Please enter a valid email.')
		elif User.query.filter_by(email=email).first():
			click.echo('Email already in use.')
		else:
			break

	while True:
		password = click.prompt('Enter Password')

		if len(password) < 8:
			click.echo("Make sure your password is at least 8 letters")
		elif re.search('[0-9]', password) is None:
			click.echo("Make sure your password has a number in it")
		elif re.search('[A-Z]', password) is None:
			click.echo("Make sure your password has a capital letter in it")
		else:
			break

	super_user = User(email, password)
	admin_role = Role.get_role('admin')

	super_user.add_role(admin_role)

	super_user.save()
	click.echo('Successfully added!')


@app.cli.command('remove_superuser')
def delete_superuser():
	email = click.prompt('Enter email')
	password = click.prompt('Enter Password')

	user = User.query.filter_by(email=email).first()
	admin = Role.query.filter_by(role='admin').first()

	if user is not None and user.check_password(password) and admin in user.role:
		db.session.delete(user)
		db.session.commit()
		click.echo('Successfully removed!')
	else:
		click.echo('Incorrect username or password')


if __name__ == '__main__':
	app.run(debug=True)
