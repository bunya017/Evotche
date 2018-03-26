# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from polls.models import BallotPaper, Category, Choice
from .forms import MyUserCreationForm, TokenUserForm, TokenForm
from .models import Token



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


def show_ballot_page(request, ball_url):
	display_ballot = BallotPaper.objects.get(ballot_url=ball_url)
	caty_list = Category.objects.filter(ballot_paper=display_ballot)
	context = {'display_ballot': display_ballot, 'caty_list': caty_list}
	return render(request, 'polls/display_ballot.html', context)


def showBallotPage(request, ball_url):
	"""Displays polls page to user who owns it"""
	display_ballot = BallotPaper.objects.get(ballot_url=ball_url)
	caty_list = Category.objects.filter(ballot_paper=display_ballot)
	context = {'display_ballot': display_ballot, 'caty_list': caty_list}
	return render(request, 'polls/displayBallot.html', context)


@login_required
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
			try:
				User.objects.get(username=user_name)
			except (User.DoesNotExist):
				return render(request, 'users/token_login.html', {'form': form, 
					'ballot': ballot, 'does_not_exist': 'This token does not exist.'})
			else:
				auth_user = User.objects.get(username=user_name)
				if (auth_user.token.ballot_paper.id == ballot.id) and (auth_user.token.is_used == False):
					login(request, auth_user)
					return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ball_url]))
				else: 
					return render(request, 'users/token_login.html', {'form': form, 
					'ballot': ballot, 'token_is_used': 'This token has been used.'})

	context = {'ballot': ballot, 'form': form}
	return render(request, 'users/token_login.html', context)


def tokens_view(request):
	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = {'ballot_list': ballot_list}
	return render(request, 'users/tokens_view.html', context)


def my_token(request, ball_url):
	ballot = BallotPaper.objects.get(ballot_url=ball_url)
	token_list = Token.objects.filter(ballot_paper__ballot_url=ball_url)
	context = {'token_list': token_list, 'ballot': ballot}
	return render(request, 'users/my_token.html', context)

