from random import choices
from string import ascii_letters, digits


def generate_random_password():
	return ''.join(choices(ascii_letters + digits, k=10))
