# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from polls.models import BallotPaper



class PurchaseInvoice(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	ballot_paper = models.ForeignKey(BallotPaper, on_delete=models.CASCADE, null=True)
	status = models.CharField(max_length=20)
	reference_code = models.CharField(max_length=250)
	date_created = models.DateTimeField(auto_now_add=True)
	due_date = models.DateField(blank=True, null=True)

	class Meta:
		ordering = ['id']

	def __str__(self):
		return self.reference_code


class Item(models.Model):
	invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE)
	item = models.CharField(max_length=100)
	description = models.CharField(max_length=100)
	unit_cost = models.IntegerField(default=0)
	quantity = models.IntegerField(default=0)
	date_added = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['date_added']

	def total(self):
		return self.unit_cost * self.unit_cost

	def __str__(self):
		return self.item

