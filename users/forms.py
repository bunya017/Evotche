from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import Token, Profile
from polls.models import BallotPaper
from django.db import transaction



class MyUserSignupForm(UserCreationForm):
	email = forms.EmailField(required=True)

	def __init__(self, *args, **kwargs):
		super(MyUserSignupForm, self).__init__(*args, **kwargs)
		self.fields['first_name'].widget = forms.TextInput(attrs={'required': True})
		self.fields['last_name'].widget = forms.TextInput(attrs={'required': True})

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

	def clean_email(self):
		email = self.cleaned_data['email']
		try:
			User.objects.get(email=email)
		except ObjectDoesNotExist:
			return email
		else:
			raise forms.ValidationError('Email is already in use.')



class UserProfileForm(forms.Form):
	first_name = forms.CharField(max_length=50, required=True)
	last_name = forms.CharField(max_length=50, required=True)
	phone = forms.CharField(max_length=50, required=True)
	organization = forms.CharField(max_length=100)


class TokenUserForm(forms.Form):
	token = forms.CharField(min_length=6, max_length=16)


class ResultCheckForm(forms.Form):
	check_result = forms.CharField(min_length=6, max_length=16)

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