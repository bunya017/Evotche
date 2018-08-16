from django import forms
from django.contrib.admin import widgets
from django.contrib.admin.widgets import AdminSplitDateTime
from django.core.exceptions import NON_FIELD_ERRORS
from PIL import Image
from django.core.files import File
from .models import Category, Choice, BallotPaper
from django.contrib.postgres.forms import DateTimeRangeField


class BallotForm(forms.ModelForm):
	start_date = forms.DateField(required=True)
	start_time = forms.TimeField(required=True)
	stop_date = forms.DateField(required=True)
	stop_time = forms.TimeField(required=True)

	def __init__(self, *args, **kwargs):
		super(BallotForm, self).__init__(*args, **kwargs)
		self.fields['start_date'].widget = forms.TextInput(attrs={'type': 'date'})
		self.fields['start_time'].widget = forms.TextInput(attrs={'type': 'time'})
		self.fields['stop_date'].widget = forms.TextInput(attrs={'type': 'date'})
		self.fields['stop_time'].widget = forms.TextInput(attrs={'type': 'time'})

	class Meta:
		model = BallotPaper
		fields = ['ballot_name', 'start_date', 'start_time', 'stop_date', 'stop_time']
		label = {'ballot_name': '', 'start_date': '', 'start_time': '', 'stop_date': '', 'stop_time': ''}


class CategoryForm(forms.ModelForm):
	def __init__(self, user, *args, **kwargs):
		super(CategoryForm, self).__init__(*args, **kwargs)
		self.fields['ballot_paper'].queryset = BallotPaper.objects.filter(
												created_by=user)
		self.fields['ballot_paper'].widget = forms.HiddenInput()

	class Meta:
		model = Category
		fields = ['ballot_paper', 'category_name']
		label = {'ballot_paper': '', 'category_name': ''}
		error_messages = {
			NON_FIELD_ERRORS: {
				'unique_together': "Sorry, you have created this category already."
			}
		}


class ChoiceForm(forms.ModelForm):
	def __init__(self, user, *args, **kwargs):
		super(ChoiceForm, self).__init__(*args, **kwargs)
		self.fields['category'].queryset = Category.objects.filter(created_by=user)
		self.fields['category'].widget   = forms.HiddenInput()

	class Meta:
		model = Choice
		fields = ['category', 'choice', 'photo']
		label = {'category': '', 'choice': '', 'photo': ''}
		error_messages = {
			NON_FIELD_ERRORS: {
				'unique_together': "Sorry, you have added this choice already."
			}
		}


class ChForm(forms.ModelForm):
	class Meta:
		model = Choice
		fields = ['category', 'choice', 'photo']



ChFormSet   = forms.inlineformset_factory(Category, Choice, form=ChForm,
				can_delete=False, extra=3)


class AddVotes(forms.Form):
	number = forms.IntegerField(required=True, min_value=0)

	def clean_number(self):
		number = self.cleaned_data['number']
		if number <+ 0:
			raise forms.ValidationError('Number must be greater than 0.')
		else:
			return number