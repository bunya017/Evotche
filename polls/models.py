# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import StringIO
from PIL import Image

from django.db import models
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile
from django_userforeignkey.models.fields import UserForeignKey



class BallotPaper(models.Model):
	ballot_name  = models.CharField(max_length=50)
	created_by   = UserForeignKey(auto_user_add=True)
	ballot_url   = models.SlugField(unique=True)
	is_photo_ballot = models.BooleanField(default=False)
	has_paid_tokens = models.BooleanField(default=False)
	has_free_tokens = models.BooleanField(default=False)
	open_date = models.DateTimeField(blank=True, null=True)
	close_date = models.DateTimeField(blank=True, null=True)
	is_protected_with_tokens = models.BooleanField(default=False)
	has_email_delivery = models.BooleanField(default=False)
	has_text_delivery = models.BooleanField(default=False)


	class Meta:
		verbose_name_plural = 'Ballot Papers'
		ordering = ['id']
		unique_together = ('ballot_name', 'created_by')

	def clean(self):
		self.ballot_name = self.ballot_name.title()

	@models.permalink
	def get_absolute_url(self):
		return 'users:show_ballot_page', (self.ballot_url)

	def is_not_open(self):
		return self.open_date > timezone.now()

	def is_opened(self):
		return self.open_date >= timezone.now() <= self.close_date

	def is_closed(self):
		return self.open_date < timezone.now() > self.close_date
	
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
		if self.photo:
			image = Image.open(StringIO.StringIO(self.photo.read()))
			image.thumbnail((360, 360), Image.ANTIALIAS)
			output = StringIO.StringIO()
			image.save(output, format='JPEG', optimize=True, quality=60)
			self.photo = InMemoryUploadedFile(output, 'ImageField', '%s.jpg' %self.photo.name, 'image/jpeg', output.len, None)

	def __str__(self):

		return self.choice

