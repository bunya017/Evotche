# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Category, Choice, BallotPaper


class ChoiceInline(admin.TabularInline):
	model = Choice
	extra = 3



class CategoryAdmin(admin.ModelAdmin):
	fieldsets = [
		(None,	{'fields': ['ballot_paper', 'category_name', 'created_by']})
	]
	inlines = [ChoiceInline]
	list_display = ['category_name', 'ballot_paper', 'created_by']


class CategoryInline(admin.TabularInline):
	model = Category


class BallotAdmin(admin.ModelAdmin):
	prepopulated_fields = {'ballot_url': ('ballot_name',)}
	fieldsets = [
		(None, {'fields': ['ballot_name', 'ballot_url', 'created_by']})
	]
	list_display = ['ballot_name', 'created_by']


admin.site.register(Category, CategoryAdmin)
admin.site.register(BallotPaper, BallotAdmin)
