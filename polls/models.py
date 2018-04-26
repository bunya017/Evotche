# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django_userforeignkey.models.fields import UserForeignKey



class BallotPaper(models.Model):
	ballot_name  = models.CharField(max_length=50)
	created_by   = UserForeignKey(auto_user_add=True)
	ballot_url   = models.SlugField(unique=True)
	is_photo_ballot = models.BooleanField(default=False)
	start_date = models.DateField(blank=True, null=True)
	start_time = models.TimeField(blank=True, null=True)
	stop_date = models.DateField(blank=True, null=True)
	stop_time = models.TimeField(blank=True, null=True)

	class Meta:
		verbose_name_plural = 'Ballot Papers'
		ordering = ['id']
		unique_together = ('ballot_name', 'created_by')

	def clean(self):
		self.ballot_name = self.ballot_name.title()

	@models.permalink
	def get_absolute_url(self):
		return 'users:show_ballot_page', (self.ballot_url)

	#def start_voting(self):
	
	def __str__(self):
		return self.ballot_name


class Category(models.Model):
	ballot_paper = models.ForeignKey(BallotPaper, on_delete=models.CASCADE)
	category_name = models.CharField(max_length=250)
	created_by = UserForeignKey(auto_user_add=True)

	class Meta:
		verbose_name_plural = 'Categories'
		ordering = ['id']
		unique_together = ('ballot_paper', 'category_name')

	def clean(self):
		self.category_name = self.category_name.title()

	def __str__(self):

		return self.category_name


class Choice(models.Model):
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	choice = models.CharField(max_length=250)
	photo = models.ImageField(upload_to='uploads/', blank=True)
	votes = models.PositiveIntegerField(default=0)

	class Meta:
		verbose_name_plural = 'Choices'
		ordering = ['id']
		unique_together = ('category', 'choice')

	def clean(self):
		self.choice = self.choice.title()

	def __str__(self):

		return self.choice


#class ImageChoice(models.Model):
#	category = models.ForeignKey(Category, on_delete=models.CASCADE)
#	choice_title = models.CharField(max_length=250)
#	choice_image = models.ImageField()