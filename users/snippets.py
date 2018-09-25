from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Token



def handle_email_file(file, ballot):
	file_list = file.split('\r\n')
	email_list = []
	mail_list = []
	errors = {}
	for email in file_list:
		try:
			validate_email(email)
		except ValidationError:
			errors[file_list.index(email) + 1] = email
		else:
			email_list.append(email)

	processed_list = check_token_email(email_list, ballot)
	emails = processed_list[0]
	exists = processed_list[1]

	return (emails, errors, exists)


def check_token_email(email_list, ballot):
	"""
	Checks if token has email or not
	"""
	exists = {}
	not_exist = []
	for email in email_list:
		try:
			Token.objects.get(ballot_paper=ballot, user__email=email)
		except Token.DoesNotExist:
			not_exist.append(email)
		else:
			exists[email_list.index(email) + 1] = email

	return (not_exist, exists)

