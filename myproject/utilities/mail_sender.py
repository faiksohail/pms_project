from myproject import mail, ADMINS
from flask_mail import Message


def send_email(recepient_email, subject, body_html, body_text):
	msg = Message(subject, sender=ADMINS[0], recipients=[recepient_email])
	msg.body = body_html
	msg.html = body_text
	mail.send(msg)
