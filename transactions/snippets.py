def make_dict(item):
	a_list = ['item', 'description', 'unit_cost', 'quantity']
	b_list = [item.item, item.description, str(item.unit_cost), str(item.quantity)]

	return dict(zip(a_list, b_list))