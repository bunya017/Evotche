from django import forms



class InvoiceForm(forms.Form):
	phone = forms.CharField(max_length=50, required=False)
	quantity = forms.IntegerField(required=True, min_value=0)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)


class FreeTokenForm(forms.Form):
	phone = forms.CharField(max_length=50, required=False)
	quantity = forms.IntegerField(required=True, min_value=0)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)