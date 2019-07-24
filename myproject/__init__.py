import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail


app = Flask(__name__)

app.config['SECRET_KEY'] = 'alpha_1996@beta_1997@gamma_1998'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysql-connector://khancirhan11:Bradykinesia242@pmsproject.cpyjal06t8wq.us-east-1.rds.amazonaws.com:3306/pmsproject'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config.update(dict(
	MAIL_SERVER = 'smtp.googlemail.com',
	MAIL_PORT = 465,
	MAIL_USE_TLS = False,
	MAIL_USE_SSL = True,
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME'),    # set MAIL_USERNAME=your-username in cmd.exe on windows
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')     # # set MAIL_PASSWORD=your-password
))

ADMINS = ['abc@gmail.com']

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

from myproject.admin.views import admin_app
from myproject.receptionist.views import receptionist_app
from myproject.doctor.views import doctor_app
from myproject.patient.views import patient_app

app.register_blueprint(admin_app, url_prefix='/admin')
app.register_blueprint(receptionist_app, url_prefix='/receptionist')
app.register_blueprint(doctor_app, url_prefix='/doctor')
app.register_blueprint(patient_app, url_prefix='/patient')

