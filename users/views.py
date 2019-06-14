# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth import login, logout, authenticate
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required, user_passes_test
from polls.models import BallotPaper, Category, Choice
from .forms import ContactForm, FreeTokenForm, MyUserSignupForm, PaidTokenForm, ResultCheckForm, TokenUserForm, UserProfileForm, EmailFileUploadForm
from .models import Token, Profile
from .snippets import handle_email_file
from polls.snippets import check_usable_password, result_avialable
from django.db.models import Q



def logout_view(request):
	logout(request)
	return HttpResponseRedirect(reverse('polls:index'))


def signup(request):
	if request.method != 'POST':
		form = MyUserSignupForm()
	else:
		form = MyUserSignupForm(data=request.POST)
		if form.is_valid():
			user = form.save()
			Profile.objects.create(user=user)
			login(request, user)
			return HttpResponseRedirect(reverse('polls:ballot'))

	context = {'form': form}
	return render(request, 'users/signup.html', context)


def contact_us(request):
	if request.method != 'POST':
		form = ContactForm()
	else:
		form = ContactForm(request.POST)

		if form.is_valid():
			contact_name = form.cleaned_data['contact_name']
			contact_email = form.cleaned_data['contact_email']
			subject = form.cleaned_data['subject']
			form_content = form.cleaned_data['content']
			email_context = {
				'contact_name': contact_name,
				'contact_email': contact_email,
				'subject': subject,
				'form_content': form_content,
			}
			template = get_template('users/contact_template.txt')
			content = template.render(email_context)
			email = EmailMessage(
				'New Contact Form Submission',
				content,
				'Evotche <no-reply@evotche.com>',
				['dollabills007@gmail.com',],
				reply_to=[contact_email],
			)
			email.send(fail_silently=False)
			return HttpResponseRedirect(reverse('users:contact_success'))

	user = request.user 
	if user.is_authenticated() and user.has_usable_password():
		base_template = 'polls/ubase.html'
	else:
		base_template = 'polls/base.html'
	context = {'form': form, 'base_template': base_template}
	return render(request, 'users/contact.html', context)


def contact_success(request):
	user = request.user 
	if user.is_authenticated() and user.has_usable_password():
		base_template = 'polls/ubase.html'
	else:
		base_template = 'polls/base.html'
	context = {'base_template': base_template}
	return render(request, 'users/contact_success.html', context,)


def new_show_ballot_page(request, ball_url):
	"""
	For ballots without tokens.
	"""
	display_ballot = BallotPaper.objects.get(ballot_url=ball_url)
	caty_list = Category.objects.filter(ballot_paper=display_ballot)
	user = request.user
	if user.is_authenticated() and user.has_usable_password():
		base_template = 'polls/ubase.html'
	else:
		base_template = 'polls/base.html'
		if display_ballot.is_opened() == False:
			context = {'base_template': base_template, 'error_message': 'The voting campaign you were looking for is not open.'}
			return render(request, 'polls/not_available.html', context)
		elif display_ballot.is_closed() == True:
			context = {'base_template': base_template, 'error_message': 'The voting campaign you were looking for is closed.'}
			return render(request, 'polls/not_available.html', context)
	context = {'display_ballot': display_ballot, 'caty_list': caty_list, 'base_template':base_template}
	return render(request, 'polls/display_ballot.html', context)


@login_required(login_url='/token/')
def show_ballot_page(request, ball_url):
	"""
	For ballots with tokens.
	"""
	display_ballot = BallotPaper.objects.get(ballot_url=ball_url)
	caty_list = Category.objects.filter(ballot_paper=display_ballot)
	user = request.user
	if user.is_authenticated() and user.has_usable_password():
		base_template = 'polls/ubase.html'
	else:
		base_template = 'polls/base.html'
	context = {'display_ballot': display_ballot, 'caty_list': caty_list, 'base_template':base_template}
	return render(request, 'polls/display_ballot.html', context)


def token_login(request):
	if request.method != 'POST':
		form = TokenUserForm()
	else:
		form = TokenUserForm(request.POST)

		if form.is_valid():
			user_name = form.cleaned_data['token']
			try:
				Token.objects.get(user=User.objects.get(username=user_name))
			except (User.DoesNotExist, Token.DoesNotExist):
				return render(request, 'users/token_login.html', {'form': form, 
					'does_not_exist': 'Please enter a valid token.'})
			else:
				auth_user = User.objects.get(username=user_name)
				ballot = auth_user.token.ballot_paper
				if auth_user.token.is_used == False:
					if ballot.is_not_open():
						return render(request, 'users/token_login.html', {'form': form, 
							'not_open': 'Sorry, this ballot box is not open for voting yet.'})
					elif ballot.is_closed() :
						return render(request, 'users/token_login.html', {'form': form, 
							'closed': 'Sorry, this ballot box is closed for voting.'})
					else: 
						login(request, auth_user)
						return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
				else:
					return render(request, 'users/token_login.html', {'form': form, 
						'token_is_used': 'This token has been used.'})

	context = {'form': form}
	return render(request, 'users/token_login.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def tokens_view(request):
	user = request.user
	# get free tokens
	if request.method != 'POST':
		free_token = FreeTokenForm(user=user)
	else:
		free_token = FreeTokenForm(request.POST, user=user)
		if free_token.is_valid():
			ballot = get_object_or_404(
				BallotPaper,
				created_by=user,
				ballot_name=free_token.cleaned_data['ballot_paper']
			)
			# Indicates that the request message is coming from tokens_view, so that
			# the back button on the buy_tokens template will point back to tokens_view
			messages.info(request, 'from tokens_view')
			return HttpResponseRedirect(reverse('trxns:get_free_tokens', args=[ballot.ballot_url]))
	# get paid tokens
	if request.method != 'POST':
		paid_token = PaidTokenForm(user=user)
	else:
		paid_token = PaidTokenForm(request.POST, user=user)
		if paid_token.is_valid():
			ballot = get_object_or_404(
				BallotPaper,
				created_by=user,
				ballot_name=paid_token.cleaned_data['ballot']
			)
			# Indicates that the request message is coming from tokens_view, so that
			# the back button on the buy_tokens template will point back to tokens_view
			messages.info(request, 'from tokens_view')
			return HttpResponseRedirect(reverse('trxns:buy_tokens', args=[ballot.ballot_url]))

	ballot_list = BallotPaper.objects.filter(created_by=request.user)
	context = { 'ballot_list': ballot_list, 'free_token': free_token, 'paid_token': paid_token }
	return render(request, 'users/tokens_view.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def my_token(request, ball_url):
	ballot = BallotPaper.objects.get(ballot_url=ball_url)
	unused_token = Token.objects.filter(ballot_paper=ballot, is_used=False)
	used_token = Token.objects.filter(ballot_paper=ballot, is_used=True)
	token_list = Token.objects.filter(ballot_paper=ballot)
	context = {'unused_token': unused_token, 'used_token': used_token, 'ballot': ballot, 'token_list': token_list}
	return render(request, 'users/my_token.html', context)


def check_results(request):
	if request.method != 'POST':
		form = ResultCheckForm()
	else:
		form = ResultCheckForm(request.POST)

		if form.is_valid():
			user_name = form.cleaned_data['check_result']
			try:
				Token.objects.get(user=User.objects.get(username=user_name))
			except (User.DoesNotExist, Token.DoesNotExist):
				return render(request, 'users/check_results.html', {'form': form, 
					'does_not_exist': 'Please enter a valid token.'})
			else:
				ballot_token = User.objects.get(username=user_name)
				ballot = ballot_token.token.ballot_paper
				close = ballot.close_date
				try:
					result_avialable(close=close, now=timezone.now())
				except (UserWarning):
					return render(request, 'users/check_results.html', {'form': form, 
												'not_public': 'Sorry, the results for this campaign is not published yet.'})
				else:
					return HttpResponseRedirect(reverse('polls:ballot_results', args=[ballot.ballot_url]))

	context = {'form': form}
	return render(request, 'users/check_results.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def update_profile(request):
	user = request.user
	if request.method != 'POST':
		form = UserProfileForm()
	else:
		form = UserProfileForm(request.POST)
		if form.is_valid():
			user.first_name = form.cleaned_data['first_name']
			user.last_name = form.cleaned_data['last_name']
			user.save()
			try:
				profile = Profile.objects.get(user=user)
			except (ObjectDoesNotExist):
				profile = Profile.objects.create(user=user)
			else:
				pass
			finally:
				profile.phone = form.cleaned_data['phone']
				profile.organization = form.cleaned_data['organization']
				profile.save()

				return HttpResponseRedirect(reverse('users:display_profile'))

	context = {'form': form}
	return render(request, 'users/update_profile.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def display_profile(request):
	user = request.user
	context = {'user': user}
	return render(request, 'users/profile.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def email_upload(request, ball_url):
	"""
	Handles the assignment of emails to tokens
	"""
	ballot = get_object_or_404(BallotPaper, created_by=request.user, ballot_url=ball_url)
	token_list = [token.user for token in Token.objects.filter(Q(ballot_paper=ballot), Q(user__email__exact=''))]

	if request.method != 'POST':
		form = EmailFileUploadForm()
	else:
		form = EmailFileUploadForm(request.POST, request.FILES)
		if form.is_valid():
			processed_txt = handle_email_file(request.FILES['file'].read(), ballot)
			email_list = processed_txt[0]
			errors = processed_txt[1]
			exists = processed_txt[2]
			diff = len(token_list) - len(email_list)

			for i in range(len(token_list)):
				try:
					token_list[i].email = email_list[i]
					token_list[i].save()
				except IndexError:
					pass

			ballot.uploaded_emails = True
			ballot.save()
			if (exists != {}) and (errors != {}):
				for line, email in sorted(errors.iteritems()):
					messages.error(request, 'Line {0}: {1}'.format(line, email), extra_tags='errors')
				for line, email in sorted(exists.iteritems()):
					messages.info(request, 'Line {0}: {1}'.format(line,email), extra_tags='exists')
			elif (errors != {}) and (exists == {}):
				for line, email in sorted(errors.iteritems()):
					messages.error(request, 'Line {0}: {1}'.format(line, email), extra_tags='errors')
			elif (exists != {}) and (errors == {}):
				for line, email in sorted(exists.iteritems()):
					messages.info(request, 'Line {0}: {1}'.format(line,email), extra_tags='exists')

			return HttpResponseRedirect(reverse('users:email_upload', args=[ballot.ballot_url]))

	context = {'form': form, 'ballot': ballot}
	return render(request, 'users/email_upload.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def get_free_tokens(request, ballot_url):
	ballot =get_object_or_404(BallotPaper, ballot_url=ballot_url)
	if request.method != 'POST':
		form = FreeTokenForm()
	else:
		form = FreeTokenForm(data=request.POST)
		if form.is_valid():
			cl_form = form.cleaned_data
			if cl_form['phone']:
				update_profile = Profile(user=request.user, phone=cl_form['phone'])
				update_profile.save()
			if cl_form['quantity'] > 20:
				context2 = {'form': form, 'ballot': ballot, 'above20': 'Sorry, you cannot get more than 20 FREE tokens.'}
				return render(request, 'users/free_tokens.html', context2)
			elif cl_form['quantity'] < 1:
				context21 = {'form': form, 'ballot': ballot, 'zero': 'Please ensure this value is greater than 0.'}
				return render(request, 'users/free_tokens.html', context21)
			ballot.has_free_tokens = True
			ballot.save()
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))

	context = {'form': form, 'ballot': ballot}
	return render(request, 'transactions/free_tokens.html', context)


"""
@user_passes_test(check_usable_password, login_url='/check-status/')
def refresh_purchase(request, ref_code):
	invoice = get_object_or_404(PurchaseInvoice, reference_code=ref_code)
	ballot = invoice.ballot_paper
	payment = Payment(key)
	payment_status = payment.get(invoice.reference_code)
	tok_list = Token.objects.filter(ballot_paper=ballot)
	tok_item = get_object_or_404(Item, invoice=invoice, item='Voter Token')
	quantity = tok_item.quantity
	salt = str(ballot.ballot_url + request.user.username + invoice.reference_code + ballot.ballot_name)

	if ballot.has_free_tokens == True:
		if len(tok_list) != 0:
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
		else:
			tokens = gen_token(salt=salt, num=quantity)
			created_tokens = User.objects.bulk_create([User(username=x) for x in tokens])
			Token.objects.bulk_create([
				Token(user=i, ballot_paper=ballot) for i in created_tokens
				]
			)
			messages.success(request, 'Voter tokens generated successfully.')
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
	else:
		if payment_status[2]['status'] == 'successful':
			ballot.has_paid_tokens = True
			ballot.save()
			if len(tok_list) != 0:
				return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
			else:
				tokens = gen_token(salt=salt, num=quantity)
				created_tokens = User.objects.bulk_create([User(username=x) for x in tokens])
				Token.objects.bulk_create([
					Token(user=i, ballot_paper=ballot) for i in created_tokens
					]
				)
				messages.success(request, 'Voter tokens generated successfully.')
				return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
		else:
			messages.error(request, 'Your payment was not successful.')
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
"""