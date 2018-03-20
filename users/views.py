# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
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


def token_login(request, ball_url):
	ballot = get_object_or_404(BallotPaper, ballot_url=ball_url)
	if request.method != 'POST':
		form = TokenUserForm()
	else:
		form = TokenUserForm(request.POST)

		if form.is_valid():
			user_name = form.cleaned_data['token']
			auth_user = get_object_or_404(User, username=user_name)
			auth_token = authenticate(username=user_name)
			if auth_user.token.ballot_paper.id == ballot.id:
				login(request, auth_token)
				return HttpResponseRedirect(reverse(
						'users:show_ballot_page', args=[ball_url]))
			else: 
				return HttpResponse('You are not allowed to vote on this campaign.')
		else:
			return HttpResponse('Token does not exist')

	context = {'form': form}
	return render(request, 'users/token_login.html', context)