from django import forms



class PurchaseForm(forms.Form):
	quantity = forms.IntegerField(required=True)
	