


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