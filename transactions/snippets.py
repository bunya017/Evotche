import requests

def make_dict(item):
	a_list = ['item', 'description', 'unit_cost', 'quantity']
	b_list = [item.item, item.description, str(item.unit_cost), str(item.quantity)]

	return dict(zip(a_list, b_list))


def makeRefCode(string):
	s_list = string.title().split()
	refCode = ''.join(s_list)
	return refCode


def auth_payant(key, imp='demo'):
	url = {
		'demo': 'https://api.demo.payant.ng',
		'live': 'https://api.payant.ng'
	}
	headers = {'Authorization': 'Bearer %s' % key}
	try:
		requests.get(url[imp], headers=headers)
	except (requests.ConnectionError):
		raise