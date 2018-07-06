# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
import datetime
from my_app.settings import PAYANT_AUTH_KEY as key
from pypayant import Client, Invoice, Payment
from polls.models import BallotPaper
from users.models import Profile, Token
from .models import PurchaseInvoice, Item
from .forms import InvoiceForm
from .snippets import make_dict
from django.shortcuts import get_object_or_404, get_list_or_404



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
			try:
				Profile.objects.get(user=user)
			except (Profile.DoesNotExist):
				messages.success(request, 'You profile details are required before you can make a purchase.')
				return render(request, 'transactions/buy_tokens.html', {'form': form, 'ballot': ballot})
			else:
				try:
					PurchaseInvoice.objects.get(ballot_paper=ballot)
				except (PurchaseInvoice.DoesNotExist):
					if (form.cleaned_data['email_delivery'] and form.cleaned_data['text_delivery']) == True:
						context = {'form': form, 'error_message': 'Sorry, you can only select one of these two.'}
						return render(request, 'transactions/buy_tokens.html', context)
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
						quantity=form.cleaned_data['quantity']
					)
					token_item.save()
					token_item_dict = make_dict(token_item)
					item_list=[token_item_dict]

					if (form.cleaned_data['email_delivery'] == True) and (form.cleaned_data['text_delivery'] == False):
						email_item = Item.objects.create(
						invoice=p_invoice,
						item='Email Delivery',
						description='Delivery of Voter Tokens via email.',
						unit_cost=1.00,
						quantity=form.cleaned_data['quantity']
						)
						email_item.save()
						email_item_dict = make_dict(email_item)
						item_list=[token_item_dict, email_item_dict]
					elif (form.cleaned_data['text_delivery'] == True) and (form.cleaned_data['email_delivery'] == False):
						text_item = Item.objects.create(
						invoice=p_invoice,
						item='Text Delivery',
						description='Delivery of Voter Tokens via text.',
						unit_cost=5.00,
						quantity=form.cleaned_data['quantity']
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


