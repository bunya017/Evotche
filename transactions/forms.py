from django import forms



class InvoiceForm(forms.Form):
	quantity = forms.IntegerField(required=True)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)


class FreeTokenForm(forms.Form):
	quantity = forms.IntegerField(required=True, max_value=30)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)