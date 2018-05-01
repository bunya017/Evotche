# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from polls.models import BallotPaper


class Token(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	ballot_paper = models.ForeignKey(BallotPaper, on_delete=models.CASCADE)
	is_used = models.BooleanField(default=False)

	class Meta:
		ordering = ['id']

	def __str__(self):
		return self.user.username


