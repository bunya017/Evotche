# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404, get_list_or_404
import datetime
from my_app.settings import PAYANT_AUTH_KEY as key
from pypayant import Client, Invoice, Payment
from polls.models import BallotPaper
from users.models import Profile, Token
from .models import PurchaseInvoice, Item
from .forms import InvoiceForm, FreeTokenForm
from .snippets import auth_payant, gen_token, make_dict, makeRefCode
from polls.snippets import check_usable_password
from requests import ConnectionError



@user_passes_test(check_usable_password, login_url='/check-status/')
def invoice_list(request):
	user = request.user
	if user.has_usable_password() == False:
		ballot = user.token.ballot_paper
		if user.token.is_token:
			return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
	invoice_list = PurchaseInvoice.objects.filter(user=user)
	context = {'invoice_list': invoice_list}
	return render(request, 'transactions/invoice_list.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def pay(request, ref_code):
	return redirect('https://demo.payant.ng/pay/%s' % (ref_code))


@user_passes_test(check_usable_password, login_url='/check-status/')
def get_invoice(request, ref_code):
	invoice = get_object_or_404(PurchaseInvoice, reference_code=ref_code)
	item_list =invoice.item_set.all()
	total = sum([item.total() for item in item_list])
	user = invoice.user
	fullname = ('%s %s' % (user.first_name, user.last_name)).title()
	if invoice.status == 'successful':
		not_paid = False
	else:
		not_paid = True
	context = {'invoice': invoice, 'total': total, 'not_paid': not_paid, 'fullname': fullname}
	return render(request, 'transactions/get_invoice.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def buy_tokens(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	user = ballot.created_by
	if request.method != 'POST':
		form = InvoiceForm()
	else:
		form = InvoiceForm(request.POST)
		if form.is_valid():
			cl_form = form.cleaned_data
			if cl_form['phone']:
				update_profile = Profile(user=request.user, phone=cl_form['phone'])
				update_profile.save()
			try:
				iv = PurchaseInvoice.objects.get(
					ballot_paper=ballot,
					ballot_paper__has_free_tokens=False,
					ballot_paper__is_paid=False
				)
			except (PurchaseInvoice.DoesNotExist):
				p_invoice = PurchaseInvoice.objects.create(
					user=request.user,
					ballot_paper=ballot,
					date_created=datetime.datetime.now(),
					due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
				)
				p_invoice.save()
				token_item = Item.objects.create(
					invoice=p_invoice,
					item='Voter Token',
					description='Voter Tokens for %s.' % (ballot.ballot_name),
					unit_cost=25.00,
					quantity=cl_form['quantity']
				)
				token_item.save()
				token_item_dict = make_dict(token_item)
				item_list=[token_item_dict]
				if (cl_form['email_delivery'] == True) and (cl_form['text_delivery'] == True):
					email_item = Item.objects.create(
						invoice=p_invoice,
						item='Email Delivery',
						description='Delivery of Voter Tokens via email.',
						unit_cost=1.00,
						quantity=cl_form['quantity']
					)
					email_item.save()
					text_item = Item.objects.create(
						invoice=p_invoice,
						item='Text Delivery',
						description='Delivery of Voter Tokens via text.',
						unit_cost=5.00,
						quantity=cl_form['quantity']
					)
					text_item.save()
					email_item_dict = make_dict(email_item)
					text_item_dict = make_dict(text_item)
					item_list=[token_item_dict, email_item_dict, text_item_dict]
				elif (cl_form['email_delivery'] == True) and (cl_form['text_delivery'] == False):
					email_item = Item.objects.create(
						invoice=p_invoice,
						item='Email Delivery',
						description='Delivery of Voter Tokens via email.',
						unit_cost=1.00,
						quantity=cl_form['quantity']
					)
					email_item.save()
					email_item_dict = make_dict(email_item)
					item_list=[token_item_dict, email_item_dict]
				elif (cl_form['text_delivery'] == True) and (cl_form['email_delivery'] == False):
					text_item = Item.objects.create(
						invoice=p_invoice,
						item='Text Delivery',
						description='Delivery of Voter Tokens via text.',
						unit_cost=5.00,
						quantity=cl_form['quantity']
					)
					text_item.save()
					text_item_dict = make_dict(text_item)
					item_list=[token_item_dict, text_item_dict]
				try:
					auth_payant(key, 'demo')
				except (ConnectionError):
					p_invoice.delete()
					context3 = {'form': form,
						'ballot': ballot,
						'conn_error': 'Network connection error, try again.'
					}
					return render(request, 'transactions/buy_tokens.html', context3)
				else:
					pay_invoice = Invoice(key)
					if request.user.profile.payant_id:
						new_invoice = pay_invoice.add(
							client_id=(request.user.profile.payant_id),
							due_date=p_invoice.due_date.strftime('%m/%d/%Y'),
							fee_bearer='account',
							items=item_list
						)
					else:
						new_client = {
							"first_name": request.user.first_name,
							"last_name": request.user.last_name,
							"email": request.user.email,
							"phone": request.user.profile.phone
						}
						new_invoice = pay_invoice.add(
							new=True,
							client=new_client,
							due_date=p_invoice.due_date.strftime('%m/%d/%Y'),
							fee_bearer='account',
							items=item_list
						)
					p_invoice.reference_code = new_invoice[2]['reference_code']
					p_invoice.status = new_invoice[2]['status']
					p_invoice.save()
					if not request.user.profile.payant_id:
						request.user.profile.payant_id = new_invoice[2]['client_id']
						request.user.profile.save()
					return HttpResponseRedirect(reverse(
						'trxns:get_invoice',
						args=[p_invoice.reference_code])
					)
			else:
				context = {'form': form,
					'ballot': ballot,
					'cant_buy': 'Sorry, you cannot buy more tokens on this ballot'
				}
				return render(request, 'transactions/buy_tokens.html', context)

	context = {'form': form, 'ballot': ballot}
	return render(request, 'transactions/buy_tokens.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def get_free_tokens(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	if request.method != 'POST':
		form = FreeTokenForm()
	else:
		form = FreeTokenForm(data=request.POST)
		if form.is_valid():
			cl_form = form.cleaned_data
			if cl_form['phone']:
				update_profile = Profile(user=request.user, phone=cl_form['phone'])
				update_profile.save()
			if cl_form['quantity'] > 30:
				context2 = {'form': form, 'ballot': ballot, 'above30': 'Sorry, you cannot get more than 30 FREE tokens.'}
				return render(request, 'transactions/free_tokens.html', context2)
			elif cl_form['quantity'] < 1:
				context21 = {'form': form, 'ballot': ballot, 'zero': 'Please ensure this value is greater than 0.'}
				return render(request, 'transactions/free_tokens.html', context21)
			try:
				iv = PurchaseInvoice.objects.get(
					ballot_paper=ballot,
					ballot_paper__has_free_tokens=False,
					ballot_paper__is_paid=False
				)
			except (PurchaseInvoice.DoesNotExist):
				if (cl_form['email_delivery'] == False) and (cl_form['text_delivery'] == False):
					f_invoice = PurchaseInvoice(
						user=request.user,
						ballot_paper=ballot,
						reference_code=makeRefCode(str('free ' + ballot.ballot_name)),
						date_created=datetime.datetime.now(),
						due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
					)
					f_invoice.status = 'successful'
					f_invoice.save()
					token_item = Item.objects.create(
						invoice=f_invoice,
						item='Voter Token',
						description='Free Voter Tokens for %s.' % (ballot.ballot_name),
						unit_cost=0.00,
						quantity=cl_form['quantity']
					)
					token_item.save()
					ballot.has_free_tokens = True
					ballot.save()
					return HttpResponseRedirect(reverse('trxns:get_invoice', args=[f_invoice.reference_code]))
				else:
					f_invoice = PurchaseInvoice(
						user=request.user,
						ballot_paper=ballot,
						date_created=datetime.datetime.now(),
						due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
					)
					f_invoice.save()
					token_item = Item.objects.create(
						invoice=f_invoice,
						item='Voter Token',
						description='Free Voter Tokens for %s.' % (ballot.ballot_name),
						unit_cost=0.00,
						quantity=cl_form['quantity']
					)
					token_item.save()
					token_item_dict = make_dict(token_item)
					item_list=[token_item_dict]

					if (cl_form['email_delivery'] == True) and (cl_form['text_delivery'] == True):
						email_item = Item.objects.create(
							invoice=f_invoice,
							item='Email Delivery',
							description='Delivery of Voter Tokens via email.',
							unit_cost=1.00,
							quantity=cl_form['quantity']
						)
						email_item.save()
						email_item_dict = make_dict(email_item)

						text_item = Item.objects.create(
							invoice=f_invoice,
							item='Text Delivery',
							description='Delivery of Voter Tokens via text.',
							unit_cost=5.00,
							quantity=cl_form['quantity']
						)
						text_item.save()
						text_item_dict = make_dict(text_item)
						item_list=[token_item_dict, email_item_dict, text_item_dict]
					elif (cl_form['email_delivery'] == True) and (cl_form['text_delivery'] == False):
						email_item = Item.objects.create(
							invoice=f_invoice,
							item='Email Delivery',
							description='Delivery of Voter Tokens via email.',
							unit_cost=1.00,
							quantity=cl_form['quantity']
						)
						email_item.save()
						email_item_dict = make_dict(email_item)
						item_list=[token_item_dict, email_item_dict]
					elif (cl_form['text_delivery'] == True) and (cl_form['email_delivery'] == False):
						text_item = Item.objects.create(
							invoice=f_invoice,
							item='Text Delivery',
							description='Delivery of Voter Tokens via text.',
							unit_cost=5.00,
							quantity=cl_form['quantity']
						)
						text_item.save()
						text_item_dict = make_dict(text_item)
						item_list=[token_item_dict, text_item_dict]

					try:
						auth_payant(key, 'demo')
					except (ConnectionError):
						f_invoice.delete()
						context3 = {'form': form, 'ballot': ballot, 'conn_error': 'Network connection error, try again.'}
						return render(request, 'transactions/free_tokens.html', context3)
					else:
						pay_invoice = Invoice(key)
						if request.user.profile.payant_id:
							new_invoice = pay_invoice.add(
								client_id=(request.user.profile.payant_id),
								due_date=f_invoice.due_date.strftime('%m/%d/%Y'),
								fee_bearer='account',
								items=item_list
							)
						else:
							new_client = {
								"first_name": request.user.first_name,
								"last_name": request.user.last_name,
								"email": request.user.email,
								"phone": request.user.profile.phone
							}
							new_invoice = pay_invoice.add(
								new=True,
								client=new_client,
								due_date=f_invoice.due_date.strftime('%m/%d/%Y'),
								fee_bearer='account',
								items=item_list
							)
						f_invoice.reference_code = new_invoice[2]['reference_code']
						f_invoice.status = new_invoice[2]['status']
						f_invoice.save()
						if not request.user.profile.payant_id:
							request.user.profile.payant_id = new_invoice[2]['client_id']
							request.user.profile.save()
						return HttpResponseRedirect(reverse(
							'trxns:get_invoice',
							args=[f_invoice.reference_code])
						)
			else:
				context = {'form': form,
					'ballot': ballot,
					'cant_buy': 'Sorry, you cannot get more tokens on this ballot'
				}
				return render(request, 'transactions/free_tokens.html', context)

	context = {'form': form, 'ballot': ballot}
	return render(request, 'transactions/free_tokens.html', context)


@user_passes_test(check_usable_password, login_url='/check-status/')
def buy_email_delivery(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	try:
		tok_len = len(Token.objects.get(ballot_paper=ballot))
	except (Token.DoesNotExist):
		messages.error(request, 'Sorry, you do not have voter tokens.')
		return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
	else:
		em_invoice = PurchaseInvoice.objects.create(
			user=request.user,
			ballot_paper=ballot,
			date_created=datetime.datetime.now(),
			due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
		)
		em_invoice.save()
		em_item = Item.objects.create(
			invoice=em_invoice,
			item='Email Delivery',
			description='Delivery of Voter Tokens via email.',
			unit_cost=1.00,
			quantity=tok_len
		)
		em_item.save()
		item_list = [make_dict(em_item)]
		try:
			auth_payant(key, 'demo')
		except (ConnectionError):
			em_invoice.delete()
			messages.error(request, 'Network connection error, try again.')
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
		else:
			pay_invoice = Invoice(key)
			new_invoice = pay_invoice.add(
				client_id=(request.user.profile.payant_id),
				due_date=em_invoice.due_date.strftime('%m/%d/%Y'),
				fee_bearer='account',
				items=item_list
			)
			em_invoice.reference_code = new_invoice[2]['reference_code']
			em_invoice.status = new_invoice[2]['status']
			em_invoice.save()
			return HttpResponseRedirect(reverse('trxns:get_invoice', args=[p_invoice.reference_code]))


@user_passes_test(check_usable_password, login_url='/check-status/')
def buy_text_delivery(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	try:
		tok_len = len(Token.objects.get(ballot_paper=ballot))
	except (Token.DoesNotExist):
		messages.error(request, 'Sorry, you do not have voter tokens.')
		return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
	else:
		tx_invoice = PurchaseInvoice.objects.create(
			user=request.user,
			ballot_paper=ballot,
			date_created=datetime.datetime.now(),
			due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
		)
		tx_invoice.save()
		tx_item = Item.objects.create(
			invoice=tx_invoice,
			item='Email Delivery',
			description='Delivery of Voter Tokens via email.',
			unit_cost=1.00,
			quantity=tok_len
		)
		tx_item.save()
		item_list = [make_dict(tx_item)]
		try:
			auth_payant(key, 'demo')
		except (ConnectionError):
			em_invoice.delete()
			messages.error(request, 'Network connection error, try again.')
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
		else:
			pay_invoice = Invoice(key)
			new_invoice = pay_invoice.add(
				client_id=(request.user.profile.payant_id),
				due_date=tx_invoice.due_date.strftime('%m/%d/%Y'),
				fee_bearer='account',
				items=item_list
			)
			em_invoice.reference_code = new_invoice[2]['reference_code']
			em_invoice.status = new_invoice[2]['status']
			em_invoice.save()
			return HttpResponseRedirect(reverse('trxns:get_invoice', args=[p_invoice.reference_code]))


@user_passes_test(check_usable_password, login_url='/check-status/')
def refresh_purchase(request, ref_code):
	invoice = PurchaseInvoice.objects.get(reference_code=ref_code)
	ballot = invoice.ballot_paper
	payment = Payment(key)
	tok_list = Token.objects.filter(ballot_paper=ballot)
	tok_item = Item.objects.get(invoice=invoice, item='Voter Token')
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
		if invoice.status != 'successful':
			messages.error(request, 'Your payment was not successful.')
			return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
		elif invoice.status == 'successful':
			ballot.is_paid = True
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

#iskjsfd