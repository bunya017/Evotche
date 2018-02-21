from django import template



register = template.Library()

@register.filter(name='add_css')
def add_css(field, css):
	class_old = field.field.widget.attrs.get('class', None)
	class_new = class_old +' '+ css if class_old else css
	return field.as_widget(attrs={'class': class_new})


@register.simple_tag(name='maxvotes')
def max_votes(votes, vote):
	if max([c.votes for c in votes]) == vote:
		return 'Winner'
	else:
		return ''
