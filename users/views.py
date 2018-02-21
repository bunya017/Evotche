# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout, authenticate
from polls.models import Category, Choice, BallotPaper
from .forms import MyUserCreationForm



def logout_view(request):
	logout(request)
	return HttpResponseRedirect(reverse('polls:index'))


def signup(request):
	if request.method != 'POST':
		form = MyUserCreationForm()
	else:
		form = MyUserCreationForm(data=request.POST)

		if form.is_valid():
			new_user = form.save()
			authenticated_user = authenticate(username=new_user.username,
					   password=request.POST['password1'])
			login(request, authenticated_user)
			return HttpResponseRedirect(reverse('polls:index'))

	context = {'form': form}
	return render(request, 'users/signup.html', context)


def show_ballot_page(request, ballot_url):
	display_ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	caty_list = Category.objects.filter(ballot_paper=display_ballot)
	context 	   = {'display_ballot': display_ballot, 'caty_list': caty_list}
	return render(request, 'polls/display_ballot.html', context)

