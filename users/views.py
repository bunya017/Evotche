# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout, authenticate
from polls.models import Category, Choice, BallotPaper
from .forms import MyUserCreationForm, TokenUserForm, TokenForm



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
	context = {'display_ballot': display_ballot, 'caty_list': caty_list}
	return render(request, 'polls/display_ballot.html', context)


def new_token(request):
	if request.method != 'POST':
		userToken = TokenUserForm()
		token = TokenForm(request.user)
	else:
		userToken = TokenUserForm(request.POST)
		token = TokenForm(request.user, request.POST)

		if userToken.is_valid() and token.is_valid():
			user_name = userToken.cleaned_data['token']
			new_userToken = User.objects.create_user(username=user_name)
			new_userToken.set_unusable_password()

			newToken = token.save(commit=False)
			newToken.user = new_userToken
			newToken.save()
			return HttpResponseRedirect(reverse('polls:index'))

	context = {'userToken': userToken, 'token': token}
	return render(request, 'users/new_token.html', context)

