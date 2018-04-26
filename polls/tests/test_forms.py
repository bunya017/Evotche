# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from polls.forms import BallotForm, CategoryForm



class BallotForm_Test(TestCase):

	def test_BallotForm_valid(self):
		form = BallotForm(data={'ballot_name': 'test box'})
		self.assertTrue(form.is_valid())

	def test_BallotForm_invalid(self):
		form = BallotForm(data={'ballot_name': ''})
		self.assertFalse(form.is_valid())


class CategoryForm_Test(TestCase):

	def test_CategoryForm_valid(self):
		form = CategoryForm(data={'ballot_paper': 'test box', 'category_name': 'category 1'})