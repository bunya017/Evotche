# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.utils.text import slugify
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.datastructures import MultiValueDictKeyError
from django.db.utils import IntegrityError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from PIL import Image
from datetime import datetime
from .models import BallotPaper, Category, Choice
from .forms import BallotForm, CategoryForm, ChForm, ChFormSet, ChoiceForm
from users.forms import TokenUserForm, ResultCheckForm
from users.models import Token
from .snippets import check_start, check_close, result_avialable



def index(request):
	if request.user.is_authenticated() and request.user.has_usable_password():
		return HttpResponseRedirect(reverse('polls:ballot'))
	# Token Form
	if request.method != 'POST':
		token_form = TokenUserForm()
	else:
		token_form = TokenUserForm(request.POST)

		if token_form.is_valid():
			user_name = token_form.cleaned_data['token']
			try:
				Token.objects.get(user=User.objects.get(username=user_name))
			except (User.DoesNotExist, Token.DoesNotExist):
				messages.success(request, 'Please enter a valid token.')
				return HttpResponseRedirect(reverse('users:token_login'))
			else:
				auth_user = User.objects.get(username=user_name)
				ballot = auth_user.token.ballot_paper
				if auth_user.token.is_used == False:
					if ballot.is_not_open():
						messages.success(request, 'Sorry, this ballot box is not open for voting yet.')
						return HttpResponseRedirect(reverse('users:token_login'))
					elif ballot.is_closed():
						messages.success(request, 'Sorry, this ballot box is closed for voting.')
						return HttpResponseRedirect(reverse('users:token_login'))
					else:
						login(request, auth_user)
						return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
				else:
					messages.success(request, 'This token has been used.')
					return HttpResponseRedirect(reverse('users:token_login'))
	# Check Results Form
	if request.method != 'POST':
		result_ckeck_form = ResultCheckForm()
	else:
		result_ckeck_form = ResultCheckForm(request.POST)

		if result_ckeck_form.is_valid():
			user_name = result_ckeck_form.cleaned_data['check_result']
			try:
				Token.objects.get(user=User.objects.get(username=user_name))
			except (User.DoesNotExist, Token.DoesNotExist):
				messages.success(request, 'Please enter a valid token.')
				return HttpResponseRedirect(reverse('users:check_results'))
			else:
				ballot_token = User.objects.get(username=user_name)
				ballot = ballot_token.token.ballot_paper
				close = ballot.close_date
				try:
					result_avialable(close=close, now=timezone.now())
				except (UserWarning):
					messages.success(request, 'Sorry, the results for this campaign is not public yet.')
					return HttpResponseRedirect(reverse('users:check_results'))
				else:
					return HttpResponseRedirect(reverse('polls:ballot_results', args=[ballot.ballot_url]))

	context = {'token_form': token_form, 'result_ckeck_form': result_ckeck_form,}
	return render(request, 'polls/index.html', context)


@login_required
def ballot(request):
	user = request.user
	if user.has_usable_password() == False:
		if user.token.is_token:
			ballot = user.token.ballot_paper
			return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = {'ballot_list': ballot_list}
	return render(request, 'polls/ballot.html', context)


@login_required
def category_view(request, ball_id):
	queryset = BallotPaper.objects.filter(created_by=request.user)
	ballot = get_object_or_404(queryset, pk=ball_id)
	context = {'ballot': ballot}
	return render(request, 'polls/category.html', context)


@login_required
def choice_view(request, cat_id):
	queryset = Category.objects.filter(created_by=request.user)
	category = get_object_or_404(queryset, pk=cat_id)
	context = {'category': category}
	return render(request, 'polls/choice_view.html', context)


@login_required(login_url='/users/token')
def vote(request, ballot_url):
	display_ballot = get_object_or_404(BallotPaper, ballot_url=ballot_url)
	queryset = Category.objects.filter(ballot_paper=display_ballot)
	caty = get_list_or_404(queryset)
	user = request.user

	for cat in caty:
		try:
			selected_choice = cat.choice_set.get(pk=request.POST[cat.category_name])
		except (KeyError, Choice.DoesNotExist, MultiValueDictKeyError):
			return render(request, 'polls/display_ballot.html', {
				'display_ballot': display_ballot,
				'error_message': 'Please select a choice across all categories.'
				})
		else:
			try:
				Token.objects.get(user=user)
			except (Token.DoesNotExist):
				return render(request, 'polls/display_ballot.html', {
					'display_ballot': display_ballot,
					'error_message': 'Sorry, you do not have authorization to vote.'
					})
			else:
				selected_choice.votes += 1
				selected_choice.save()
				if not display_ballot.is_open:
					display_ballot.is_open = True
					display_ballot.save() 
				user.token.is_used = True
				user.token.save()
				logout(request)
	
	return HttpResponseRedirect(reverse('polls:vote_success'))


def vote_success(request):
	return render(request, 'polls/vote_success.html')


@login_required
def results(request):
	user = request.user
	if user.has_usable_password() == False:
		ballot = user.token.ballot_paper
		if user.token.is_token:
			return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = {'ballot_list': ballot_list}
	return render(request, 'polls/results.html', context)


def ballot_results(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	caty_list = Category.objects.filter(ballot_paper=ballot)
	user = request.user 
	if user.is_authenticated() and user.has_usable_password():
		base_template = 'polls/ubase.html'
	else:
		base_template = 'polls/base.html'
	context = {'caty_list': caty_list, 'ballot': ballot, 'base_template': base_template}
	return render(request, 'polls/ballot_result.html', context)


@login_required
def show_results_public(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	if ballot.show_results_to_public == False:
		ballot.show_results_to_public = True
		ballot.save()
	else:
		ballot.show_results_to_public = False
		ballot.save()

	return HttpResponseRedirect(reverse('polls:category_view', args=[ballot.id]))


@login_required
def add_new_ballot(request):
	user = request.user
	now = datetime.now()
	if user.has_usable_password() == False:
		ballot = user.token.ballot_paper
		if user.token.is_token:
			return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
	if request.method != 'POST':
		form = BallotForm()
	else:
		form = BallotForm(request.POST)
		if form.is_valid():
			start_date= form.cleaned_data['start_date']
			start_time= form.cleaned_data['start_time']
			stop_date= form.cleaned_data['stop_date']
			stop_time= form.cleaned_data['stop_time']
			start = datetime.combine(start_date, start_time)
			close = datetime.combine(stop_date, stop_time)
			try:
				new_ballot = form.save(commit=False)
				new_ballot.created_by = request.user
				new_ballot.ballot_url = slugify(request.user.username +' '+ new_ballot.ballot_name)
				new_ballot.open_date = check_start(start, now)
				new_ballot.close_date = check_close(close, start)
				new_ballot.save()
			except (IntegrityError):
				return render(request, 'polls/new_ballot.html', {'form': form, 'error_message': 'Sorry, you have created this box already.'})
			except (AssertionError):
				return render(request, 'polls/new_ballot.html', {'form': form, 'error_message': 'Sorry, you can\'t set open time less than now.'})
			except (ZeroDivisionError):
				return render(request, 'polls/new_ballot.html', {'form': form, 'error_message': 'Sorry, you can\'t set close time less than open time.'})
			else:
				return HttpResponseRedirect(reverse('polls:category_view', args=[new_ballot.id]))
	context = {'form': form}
	return render(request, 'polls/new_ballot.html', context)


@login_required
def add_new_caty(request, ball_id):
	ballot = get_object_or_404(BallotPaper, created_by=request.user, pk=ball_id)
	initial_dict = {'ballot_paper': ballot}
	if request.method != 'POST':
		form 	= CategoryForm(request.user, initial=initial_dict)
		chForms = ChFormSet(prefix='ch')
	else:
		form 	= CategoryForm(request.user, request.POST, initial=initial_dict)
		chForms = ChFormSet(request.POST, request.FILES, prefix='ch')
		if form.is_valid():
			new_caty = form.save(commit=False)
			new_caty.created_by = request.user
			new_caty.save()
			chForms.instance = new_caty
			chForms.save()
			return HttpResponseRedirect(reverse('polls:category_view', args=[ball_id]))

	context = {'ballot': ballot, 'form': form, 'chForms': chForms}
	return render(request, 'polls/new_caty.html', context)


@login_required
def add_new_choice(request, cat_id):
	category = get_object_or_404(Category, created_by=request.user, pk=cat_id)
	initial_dict = {'category': category}
	if request.method != 'POST':
		form = ChoiceForm(request.user, initial=initial_dict)
	else:
		form = ChoiceForm(request.user, request.POST, request.FILES, initial=initial_dict)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(reverse('polls:choice_view', args=[cat_id]))

	context = {'category': category, 'form': form}
	return render(request, 'polls/new_choice.html', context)


@login_required
def delete_ballot(request, ball_id):
	ballot = get_object_or_404(BallotPaper, created_by=request.user, pk=ball_id)
	categories = ballot.category_set.all()
	for category in categories:
		choices = category.choice_set.all()
		for choice in choices:
			if choice.photo:
				choice.photo.delete(save=False)
	ballot.delete()
	return HttpResponseRedirect(reverse('polls:ballot'))


@login_required
def delete_caty(request, cat_id):
	category = get_object_or_404(Category, pk=cat_id)
	ball_id  = category.ballot_paper_id
	choices = category.choice_set.all()
	for choice in choices:
		if choice.photo:
			choice.photo.delete(save=False)
	category.delete()
	return HttpResponseRedirect(reverse('polls:category_view', args=[ball_id,]))


@login_required
def delete_choice(request, ch_id):
	choice = get_object_or_404(Choice, pk=ch_id)
	cat_id = choice.category_id
	if choice.photo:
		choice.photo.delete(save=False)
	choice.delete()
	return HttpResponseRedirect(reverse('polls:choice_view', args=[cat_id,]))


def pricing(request):
	return render(request, 'polls/pricing.html')


def toggle_ballot(request, ballot_url):
	ballot = get_object_or_404(BallotPaper, created_by=request.user, ballot_url=ballot_url)
	if ballot.is_open == False:
		ballot.is_not_open = False
		ballot.is_open = True
		ballot.is_closed = False
		ballot.save()
	else:
		ballot.is_not_open = False
		ballot.is_open = False
		ballot.is_closed = True
		ballot.save()

	return HttpResponseRedirect(reverse('polls:category_view', args=[ballot.id]))