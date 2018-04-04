from django import template



register = template.Library()

@register.filter(name='add_css')
def add_css(field, css):
	widgs = field.field.widget.attrs
	attr_list = css.split(',')
	for attr in attr_list:
		css1 = attr.split(':')
		widgs[css1[0]] = css1[1]

	rendered = str(field)
	return rendered


@register.simple_tag(name='maxvotes')
def max_votes(votes, vote):
	if max([c.votes for c in votes]) == vote:
		return 'Winner'
	else:
		return ''
