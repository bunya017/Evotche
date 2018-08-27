# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import wraps
from PIL import Image
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.forms.models import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.text import slugify
from .forms import AddVotes, BallotForm, CategoryForm, ChForm, ChFormSet, ChoiceForm
from .models import BallotPaper, Category, Choice
from .snippets import check_close, check_start, check_usable_password, gen_url, result_avialable
from transactions.models import PurchaseInvoice
from users.forms import ResultCheckForm, TokenUserForm
from users.models import Token



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
				messages.error(request, 'Please enter a valid token.')
				return HttpResponseRedirect(reverse('users:token_login'))
			else:
				auth_user = User.objects.get(username=user_name)
				ballot = auth_user.token.ballot_paper
				if auth_user.token.is_used == False:
					if ballot.is_not_open():
						messages.error(request, 'Sorry, this ballot box is not open for voting yet.')
						return HttpResponseRedirect(reverse('users:token_login'))
					elif ballot.is_closed():
						messages.error(request, 'Sorry, this ballot box is closed for voting.')
						return HttpResponseRedirect(reverse('users:token_login'))
					else:
						login(request, auth_user)
						return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
				else:
					messages.error(request, 'This token has been used.')
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
				messages.error(request, 'Please enter a valid token.')
				return HttpResponseRedirect(reverse('users:check_results'))
			else:
				ballot_token = User.objects.get(username=user_name)
				ballot = ballot_token.token.ballot_paper
				close = ballot.close_date
				try:
					result_avialable(close=close, now=timezone.now())
				except (UserWarning):
					messages.error(request, 'Sorry, the results for this campaign is not public yet.')
					return HttpResponseRedirect(reverse('users:check_results'))
				else:
					return HttpResponseRedirect(reverse('polls:ballot_results', args=[ballot.ballot_url]))

	context = {'token_form': token_form, 'result_ckeck_form': result_ckeck_form,}
	return render(request, 'polls/index.html', context)


def pricing(request):
	return render(request, 'polls/pricing.html')


def privacy(request):
	return render(request, 'polls/privacy.html')

def terms(request):
	return render(request, 'polls/terms.html')


def check_login_then_logout(request):
	if request.user.is_authenticated():
		logout(request)
		messages.error(request, 'Access denied, please log into your account.')
	return HttpResponseRedirect(reverse('users:login'))


@user_passes_test(check_usable_password, login_url='/check-status/')
def ballot(request):
	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = {'ballot_list': ballot_list}
	return render(request, 'polls/ballot.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def category_view(request, ball_id):
	queryset = BallotPaper.objects.filter(created_by=request.user)
	ballot = get_object_or_404(queryset, pk=ball_id)
	context = {'ballot': ballot}
	return render(request, 'polls/category.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def choice_view(request, cat_id):
	queryset = Category.objects.filter(created_by=request.user)
	category = get_object_or_404(queryset, pk=cat_id)
	context = {'category': category}
	return render(request, 'polls/choice_view.html', context)


def new_vote(request, ballot_url):
	"""
	For ballots without tokens.
	"""
	display_ballot = get_object_or_404(BallotPaper, ballot_url=ballot_url)
	queryset = Category.objects.filter(ballot_paper=display_ballot)
	caty = get_list_or_404(queryset)

	for cat in caty:
		try:
			selected_choice = cat.choice_set.get(pk=request.POST[cat.category_name])
		#except (KeyError, Choice.DoesNotExist):
		#	return render(request, 'polls/display_ballot.html', {
		#		'display_ballot': display_ballot,
		#		'error_message': 'Please select a valid choice.'
		#	})
		except (MultiValueDictKeyError):
			pass
		else:
			selected_choice.votes += 1
			selected_choice.save()

	return HttpResponseRedirect(reverse('polls:vote_success'))


@login_required(login_url='/token/')
def vote(request, ballot_url):
	"""
	For ballots with tokens.
	"""
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
				logout(user)

	
	return HttpResponseRedirect(reverse('polls:vote_success'))


def vote_success(request):
	return render(request, 'polls/vote_success.html')


@user_passes_test(check_usable_password, login_url='/check-status/')
def results(request):
	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = {'ballot_list': ballot_list}
	return render(request, 'polls/results.html', context)


def ballot_results(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	caty_list = Category.objects.filter(ballot_paper=ballot)
	user = request.user 
	if user == ballot.created_by:
		base_template = 'polls/ubase.html'
	else:
		base_template = 'polls/base.html'
		if ballot.is_opened() == False:
			context = {'base_template': base_template, 'error_message': 'Oops! This voting campaign is not open yet.'}
			return render(request, 'polls/not_available.html', context)
		elif ballot.is_closed() == True:
			context = {'base_template': base_template, 'error_message': 'Oops! This voting campaign is closed.'}
			return render(request, 'polls/not_available.html', context)

	context = {'caty_list': caty_list, 'ballot': ballot, 'base_template': base_template}
	return render(request, 'polls/ballot_result.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def show_results_public(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	if ballot.show_results_to_public == False:
		ballot.show_results_to_public = True
		ballot.save()
	else:
		ballot.show_results_to_public = False
		ballot.save()

	return HttpResponseRedirect(reverse('polls:category_view', args=[ballot.id]))


@user_passes_test(check_usable_password, login_url='/check-status/')
def add_new_ballot(request):
	user = request.user
	now = datetime.now()
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
				#new_ballot.ballot_url = slugify(request.user.username +' '+ new_ballot.ballot_name)
				new_ballot.open_date = check_start(start, now)
				new_ballot.close_date = check_close(close, start)
				new_ballot.save()
				salt = str(request.user) + str(new_ballot.ballot_name) + datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
				new_ballot.ballot_url = gen_url(salt=salt, id=new_ballot.pk)
				new_ballot.save()
			except (IntegrityError):
				return render(request, 'polls/new_ballot.html', {'form': form, 'context': 'Sorry, you have created this box already.'})
			except (AssertionError):
				return render(request, 'polls/new_ballot.html', {'form': form, 'error_message': 'Sorry, you can\'t set open time less than now.'})
			except (ZeroDivisionError):
				return render(request, 'polls/new_ballot.html', {'form': form, 'error_message': 'Sorry, you can\'t set close time less than open time.'})
			else:
				return HttpResponseRedirect(reverse('polls:category_view', args=[new_ballot.id]))
	context = {'form': form}
	return render(request, 'polls/new_ballot.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
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


@user_passes_test(check_usable_password, login_url='/check-status/')
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


@user_passes_test(check_usable_password, login_url='/check-status/')
def delete_ballot(request, ball_id):
	ballot = get_object_or_404(BallotPaper, created_by=request.user, pk=ball_id)
	categories = len(ballot.category_set.all())
	invoices = len(PurchaseInvoice.objects.filter(ballot_paper=ballot))
	tokens = len(Token.objects.filter(ballot_paper=ballot))
	context = {
		'ballot': ballot, 
		'categories': categories, 
		'invoices': invoices,
		'tokens': tokens,
	}
	return render(request, 'polls/delete_ballot.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def confirm_ballot(request, ball_id):
	"""Delete is final"""
	ballot = get_object_or_404(BallotPaper, created_by=request.user, pk=ball_id)
	categories = ballot.category_set.all()
	if request.method != 'POST':
		return HttpResponseRedirect(reverse('polls:delete_ballot', args=[ballot.id]))
	else:
		if 'Yes' == str(request.POST.get('poster')):
			for category in categories:
				choices = category.choice_set.all()
				for choice in choices:
					if choice.photo:
						choice.photo.delete(save=False)
			ballot.delete()
			return HttpResponseRedirect(reverse('polls:ballot'))
		else:
			return HttpResponseRedirect(reverse('polls:delete_ballot', args=[ballot.id]))


@user_passes_test(check_usable_password, login_url='/check-status/')
def delete_caty(request, cat_id):
	category = get_object_or_404(Category, pk=cat_id)
	ballot  = category.ballot_paper
	choices = category.choice_set.all()
	context = {'ballot': ballot, 'category': category, 'choices': choices}
	return render(request, 'polls/delete_caty.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def confirm_caty(request, cat_id):
	"""Delete is final"""
	category = get_object_or_404(Category, pk=cat_id)
	ballot  = category.ballot_paper
	choices = category.choice_set.all()
	if request.method != 'POST':
		return HttpResponseRedirect(reverse('polls:delete_caty', args=[category.id]))
	else:
		if 'Yes' == str(request.POST.get('poster')):
			for choice in choices:
				if choice.photo:
					choice.photo.delete(save=False)
			category.delete()
			return HttpResponseRedirect(reverse('polls:category_view', args=[ballot.id,]))
		else:
			return HttpResponseRedirect(reverse('polls:delete_caty', args=[category.id]))


@user_passes_test(check_usable_password, login_url='/check-status/')
def delete_choice(request, ch_id):
	choice = get_object_or_404(Choice, pk=ch_id)
	category = choice.category
	context = {'choice': choice, 'category': category}
	return render(request, 'polls/delete_choice.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def confirm_choice(request, ch_id):
	"""Delete is final"""
	choice = get_object_or_404(Choice, pk=ch_id)
	category = choice.category
	if request.method != 'POST':
		return HttpResponseRedirect(reverse('polls:delete_choice', args=[choice.id]))
	else:
		if 'Yes' == str(request.POST.get('poster')):
			if choice.photo:
				choice.photo.delete(save=False)
			choice.delete()
			return HttpResponseRedirect(reverse('polls:choice_view', args=[category.id]))
		else:
			return HttpResponseRedirect(reverse('polls:delete_choice', args=[choice.id]))


@user_passes_test(check_usable_password, login_url='/check-status/')
def add_votes(request, ch_id):
	choice = Choice.objects.get(pk=ch_id)
	
	if request.method != 'POST':
		form = AddVotes()
	else:
		form = AddVotes(request.POST)
		if form.is_valid():
			num = form.cleaned_data['number']
			choice.votes += num
			choice.save()
			return HttpResponseRedirect(reverse('polls:choice_view', args=[choice.category.id]))

	context = {'choice': choice, 'form': form}
	return render(request, 'polls/add_votes.html', context)
