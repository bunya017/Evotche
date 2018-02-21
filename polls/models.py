# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django_userforeignkey.models.fields import UserForeignKey



class BallotPaper(models.Model):
	ballot_name  = models.CharField(max_length=50, unique=True)
	created_by   = UserForeignKey(auto_user_add=True)
	ballot_url   = models.SlugField(unique=True)

	class Meta:
		verbose_name_plural = 'Ballot Papers'
		ordering = ['id']

	@models.permalink
	def get_absolute_url(self):
		return 'users:show_ballot_page', (self.slug_field,)
	
	def __str__(self):
		return self.ballot_name


class Category(models.Model):
	ballot_paper = models.ForeignKey(BallotPaper, on_delete=models.CASCADE)
	category_name = models.CharField(max_length=250)
	created_by = UserForeignKey(auto_user_add=True)

	class Meta:
		verbose_name_plural = 'Categories'
		ordering = ['id']

	def __str__(self):

		return self.category_name


class Choice(models.Model):
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	choice = models.CharField(max_length=250)
	votes = models.PositiveIntegerField(default=0)

	class Meta:
		verbose_name_plural = 'Choices'
		ordering = ['id']

	def __str__(self):

		return self.choice