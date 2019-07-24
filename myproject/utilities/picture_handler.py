import os
from flask import current_app
from random import choices
from string import ascii_letters


def upload_picture(file, user_id, test_id):

	filename = file.filename

	ext_type = filename.split('.')[-1]  # extension of the file like jpeg, png

	random_sequence = ''.join(choices(ascii_letters, k=10))

	storage_filename = f'{str(user_id)}{str(test_id)}{random_sequence}.{ext_type}'   # change the filename to user_id,test_id.extension

	filepath = os.path.join(current_app.root_path, 'static/uploads', storage_filename)

	file.save(filepath)

	return storage_filename


def remove_picture(filename):
	try:
		os.remove(os.path.join(current_app.root_path, 'static/uploads', filename))
		return True
	except:
		return False
