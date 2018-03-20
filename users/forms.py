from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Token
from polls.models import BallotPaper
from django.db import transaction


class MyUserCreationForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

	def save(self, commit=True):
		user = super(MyUserCreationForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


class TokenUserForm(forms.Form):
		token = forms.CharField(min_length=6, max_length=16)


class TokenForm(forms.ModelForm):
	def __init__(self, user, *args, **kwargs):
		super(TokenForm, self).__init__(*args, **kwargs)
		#self.fields['user'].
		self.fields['ballot_paper'].queryset = BallotPaper.objects.filter(created_by=user)

	class Meta:
		model = Token
		fields = ('ballot_paper', 'is_token')


token_text = forms.CharField(min_length=6, max_length=16)