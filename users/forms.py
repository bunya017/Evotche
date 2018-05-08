from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import Token
from polls.models import BallotPaper
from django.db import transaction



class MyUserSignupForm(forms.Form):
	username = forms.CharField(max_length=30, required=True)
	email = forms.EmailField(required=True)
	password = forms.CharField(widget=forms.PasswordInput(), required=True)

	def clean_username(self):
		username = self.cleaned_data['username']
		try:
			User.objects.get(username=username)
		except ObjectDoesNotExist:
			return username
		else:
			raise forms.ValidationError('Username is already taken.')

	def clean_email(self):
		email = self.cleaned_data['email']
		try:
			User.objects.get(email=email)
		except ObjectDoesNotExist:
			return email
		else:
			raise forms.ValidationError('Email is already taken.')


class TokenUserForm(forms.Form):
	token = forms.CharField(min_length=6, max_length=16)


class TokenNumForm(forms.Form):
	number_of_tokens = forms.IntegerField()


class TokenForm(forms.ModelForm):
	def __init__(self, user, *args, **kwargs):
		super(TokenForm, self).__init__(*args, **kwargs)
		self.fields['ballot_paper'].queryset = BallotPaper.objects.filter(created_by=user)
		#self.fields['ballot_paper'].widget = forms.HiddenInput()

	class Meta:
		model = Token
		fields = ('ballot_paper',)

class ContactForm(forms.Form):
	contact_name = forms.CharField(max_length=60, required=True, strip=True)
	contact_email = forms.EmailField(required=True)
	subject = forms.CharField(max_length=50, required=True)
	content = forms.CharField(required=True, widget=forms.Textarea)