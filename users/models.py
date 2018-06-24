# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from polls.models import BallotPaper


class Token(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	ballot_paper = models.ForeignKey(BallotPaper, on_delete=models.CASCADE)
	is_used = models.BooleanField(default=False)
	is_token = models.BooleanField(default=True)

	class Meta:
		ordering = ['id']

	def is_used(self):
		return self.is_used

	def __str__(self):
		return self.user.username


class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	payant_id = models.IntegerField(null=True ,blank=True)
	phone = models.CharField(max_length=50)
	organization = models.CharField(max_length=75)

	class Meta:
		ordering = ['id']

	def __str__(self):
		return self.user.username