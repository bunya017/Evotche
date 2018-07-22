from django import forms
from users.models import Profile



class InvoiceForm(forms.Form):
	phone = forms.CharField(max_length=50, required=False)
	quantity = forms.IntegerField(required=True, min_value=0)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)

	def clean_phone(self):
		phone = self.cleaned_data['phone']
		try:
			Profile.objects.get(phone=phone)
		except (Profile.DoesNotExist):
			return phone
		else:
			raise forms.ValidationError('Phone number is already in use.')



class FreeTokenForm(forms.Form):
	phone = forms.CharField(max_length=50, required=False)
	quantity = forms.IntegerField(required=True, min_value=0)
	email_delivery = forms.BooleanField(required=False)
	text_delivery = forms.BooleanField(required=False)

	def clean_phone(self):
		phone = self.cleaned_data['phone']
		try:
			Profile.objects.get(phone=phone)
		except (Profile.DoesNotExist):
			return phone
		else:
			raise forms.ValidationError('Phone number is already in use.')
