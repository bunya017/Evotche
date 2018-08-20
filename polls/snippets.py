from hashids import Hashids



def check_start(start, now):
	try:
		assert start >= now
	except AssertionError:
		raise
	else:
		return start


def check_close(close, start):
	try:
		assert close > start
	except AssertionError:
		raise ZeroDivisionError
	else:
		return close


def result_avialable(close, now):
	try:
		assert now > close
	except AssertionError:
		raise UserWarning


def gen_url(salt, id):
	hashid = Hashids(min_length=10, salt=salt, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
	return hashid.encode(id)