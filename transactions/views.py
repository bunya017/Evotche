# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import datetime
from my_app.settings import PAYANT_AUTH_KEY as key
from pypayant import Client, Invoice, Payment
from polls.models import BallotPaper
from users.models import Profile, Token
from .models import PurchaseInvoice, Item
from .forms import PurchaseForm



def pay(request, ref_code):
	return redirect('https://demo.payant.ng/pay/%s' % (ref_code))


@login_required
def buy_tokens(request, ballot_url):
	ballot = BallotPaper.objects.get(ballot_url=ballot_url)
	user = ballot.created_by
	if request.method != 'POST':
		form = PurchaseForm()
	else:
		form = PurchaseForm(request.POST)
		if form.is_valid():
			p_invoice = PurchaseInvoice.objects.create(
				user=user,
				ballot_paper=ballot,
				date_created=datetime.datetime.now(),
				due_date=datetime.datetime.now().date() + datetime.timedelta(days=2)
			)
			p_invoice.save()
			item = Item.objects.create(
				invoice=p_invoice,
				item='Voter Token',
				description='Voter Tokens for %s ballot box' % (ballot.ballot_name),
				unit_cost=35.00,
				quantity=form.cleaned_data['quantity']
			)
			item.save()
			pay_invoice = Invoice(key)
			new_invoice = pay_invoice.add(
				client_id=(user.profile.payant_id),
				due_date=p_invoice.due_date.strftime('%m/%d/%Y'),
				fee_bearer='account',
				items=[{
					'item': item.item,
					'description': item.description,
					'unit_cost': str(item.unit_cost),
					'quantity': str(item.quantity)
				}]
			)
			p_invoice.status = new_invoice[2]['status']
			p_invoice.reference_code = new_invoice[2]['reference_code']
			p_invoice.save()
			return HttpResponseRedirect(reverse('trxns:pay', args=[p_invoice.reference_code]))

	context = {'form': form}
	return render(request, 'transactions/buy_tokens.html', context)