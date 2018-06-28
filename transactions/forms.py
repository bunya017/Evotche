from django import forms



class InvoiceForm(forms.Form):
	quantity = forms.IntegerField(required=True)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)
