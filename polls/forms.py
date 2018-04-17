from django import forms
from django.contrib.admin import widgets
from django.core.exceptions import NON_FIELD_ERRORS
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import Category, Choice, BallotPaper


class BallotForm(forms.ModelForm):
	class Meta:
		model = BallotPaper
		fields = ['ballot_name']
		label = {'ballot_name': ''}


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


class ChForm(forms.ModelForm):
	class Meta:
		model = Choice
		fields = ['category', 'choice', 'photo']



ChFormSet   = forms.inlineformset_factory(Category, Choice, form=ChForm,
				can_delete=False, extra=3)
