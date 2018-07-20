# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
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
from .snippets import auth_payant, make_dict, makeRefCode
from requests import ConnectionError



def invoice_list(request):
	user = request.user
	if user.has_usable_password() == False:
		ballot = user.token.ballot_paper
		if user.token.is_token:
			return HttpResponseRedirect(reverse('users:show_ballot_page', args=[ballot.ballot_url]))
	invoice_list = PurchaseInvoice.objects.filter(user=user)
	context = {'invoice_list': invoice_list}
	return render(request, 'transactions/invoice_list.html', context)


def pay(request, ref_code):
	return redirect('https://demo.payant.ng/pay/%s' % (ref_code))


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


@login_required
def buy_tokens(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	user = ballot.created_by
	if request.method != 'POST':
		form = InvoiceForm()
	else:
		form = InvoiceForm(request.POST)
		if form.is_valid():
			cl_form = form.cleaned_data
			try:
				Profile.objects.get(user=user)
			except (Profile.DoesNotExist):
				messages.success(request, 'You profile details are required before you can make a purchase.')
				return render(request, 'transactions/buy_tokens.html', {'form': form, 'ballot': ballot})
			else:
				try:
					PurchaseInvoice.objects.get(ballot_paper=ballot)
				except (PurchaseInvoice.DoesNotExist):
					if (cl_form['email_delivery'] and cl_form['text_delivery']) == True:
						contextg = {'form': form, 'error_message': 'Sorry, you can only select one of these two.'}
						return render(request, 'transactions/buy_tokens.html', contextg)
					p_invoice = PurchaseInvoice.objects.create(
						user=user,
						ballot_paper=ballot,
						date_created=datetime.datetime.now(),
						due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
					)
					p_invoice.save()
					token_item = Item.objects.create(
						invoice=p_invoice,
						item='Voter Token',
						description='Voter Tokens for %s.' % (ballot.ballot_name),
						unit_cost=35.00,
						quantity=cl_form['quantity']
					)
					token_item.save()
					token_item_dict = make_dict(token_item)
					item_list=[token_item_dict]

					if (cl_form['email_delivery'] == True) and (cl_form['text_delivery'] == False):
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
					
					pay_invoice = Invoice(key)
					new_invoice = pay_invoice.add(
						client_id=(user.profile.payant_id),
						due_date=p_invoice.due_date.strftime('%m/%d/%Y'),
						fee_bearer='account',
						items=item_list
					)
					p_invoice.reference_code = new_invoice[2]['reference_code']
					p_invoice.status = new_invoice[2]['status']
					p_invoice.save()
					return HttpResponseRedirect(reverse('trxns:get_invoice', args=[p_invoice.reference_code]))
				else:
					context1 = {'form': form, 'cant_buy': 'This box has voter tokens already! You cannot buy more.'}
					return render(request, 'transactions/buy_tokens.html', context1)

	context = {'form': form, 'ballot': ballot}
	return render(request, 'transactions/buy_tokens.html', context)


@login_required
def get_free_tokens(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	if request.method == 'POST':
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
						return HttpResponseRedirect(reverse('trxns:get_invoice', args=[f_invoice.reference_code]))
			else:
				return HttpResponseRedirect(reverse('trxns:get_invoice', args=[iv.reference_code]))
	else:
		form = FreeTokenForm()

	context = {'form': form, 'ballot': ballot}
	return render(request, 'transactions/free_tokens.html', context)


def refresh_purchase(request, ref_code):
	invoice = PurchaseInvoice.objects.get(reference_code=ref_code)
	ballot = invoice.ballot_paper
	payment = Payment(key)

	# paymentDate = payment[2]['transaction_date']

	if (ballot.is_paid) and len(Token.objects.filter(ballot_paper=ballot)):
		return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
	elif invoice.status != 'successful':
		messages.success(request, 'Your payment was not successful.')
		return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))
	elif invoice.status == 'successful':
		ballot.is_paid = True
		ballot.save()
		return HttpResponseRedirect(reverse('users:my_token', args=[ballot.ballot_url]))


