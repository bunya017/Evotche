# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Max
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.utils.text import slugify
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.datastructures import MultiValueDictKeyError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import BallotPaper, Category, Choice
from .forms import BallotForm, CategoryForm, ChForm, ChFormSet, ChoiceForm




def index(request):

	return render(request, 'polls/index.html')


@login_required
def ballot(request):
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


def vote(request, ballot_url):
	display_ballot = get_object_or_404(BallotPaper, ballot_url=ballot_url)
	queryset = Category.objects.filter(ballot_paper=display_ballot)
	caty = get_list_or_404(queryset)

	for cat in caty:
		try:
			selected_choice = cat.choice_set.get(pk=request.POST[cat.category_name])
		except (KeyError, Choice.DoesNotExist, MultiValueDictKeyError):
			return render(request, 'polls/display_ballot.html', {
				'display_ballot': display_ballot,
				'error_message': 'Please select a choice across all categories.'
				})
		else:
			selected_choice.votes += 1
			selected_choice.save()
	
	return HttpResponseRedirect(reverse('polls:index'))


@login_required
def results(request):
	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = {'ballot_list': ballot_list}
	return render(request, 'polls/results.html', context)


def ballot_results(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	caty_list = Category.objects.filter(ballot_paper=ballot)
	context = {'caty_list': caty_list, 'ballot': ballot}
	return render(request, 'polls/ballot_result.html', context)


@login_required
def add_new_ballot(request):
	if request.method != 'POST':
		form = BallotForm()
	else:
		form = BallotForm(request.POST)
		if form.is_valid():
			new_ballot = form.save(commit=False)
			new_ballot.created_by = request.user
			new_ballot.ballot_url = slugify(new_ballot.ballot_name)
			new_ballot.save()
			return HttpResponseRedirect(reverse('polls:category_view', 
													args=[new_ballot.id]))

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
		chForms = ChFormSet(request.POST, prefix='ch')
		if form.is_valid():
			new_caty = form.save(commit=False)
			new_caty.created_by = request.user
			new_caty.save()

			chForms.instance = new_caty
			chForms.save()
			return HttpResponseRedirect(reverse('polls:category_view', 
											args=[ball_id]))

	context = {'ballot': ballot, 'form': form, 'chForms': chForms}
	return render(request, 'polls/new_caty.html', context)


@login_required
def add_new_choice(request, cat_id):
	category = get_object_or_404(Category, created_by=request.user, pk=cat_id)
	initial_dict = {'category': category}
	if request.method != 'POST':
		form = ChoiceForm(request.user, initial=initial_dict)
	else:
		form = ChoiceForm(request.user, request.POST, initial=initial_dict)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(reverse('polls:choice_view', 
													args=[cat_id]))

	context = {'category': category, 'form': form}
	return render(request, 'polls/new_choice.html', context)


@login_required
def delete_ballot(request, ball_id):

	BallotPaper.objects.filter(created_by=request.user, pk=ball_id).delete()
	return HttpResponseRedirect(reverse('polls:ballot'))


@login_required
def delete_caty(request, cat_id):
	category = get_object_or_404(Category, pk=cat_id)
	ball_id  = category.ballot_paper_id 
	category.delete()
	return HttpResponseRedirect(reverse('polls:category_view', args=[ball_id,]))


@login_required
def delete_choice(request, ch_id):

	choice = get_object_or_404(Choice, pk=ch_id)
	cat_id = choice.category_id
	choice.delete()
	return HttpResponseRedirect(reverse('polls:choice_view', args=[cat_id,]))


#def max_votes(request cat_id):
#	choices = Choice.objects.filter(category_id=cat_id)
#	winner = choices.aggregate(Max('votes'))
#	return winner