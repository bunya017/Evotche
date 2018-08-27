# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Category, Choice, BallotPaper


class ChoiceInline(admin.TabularInline):
	model = Choice
	extra = 3


class CategoryAdmin(admin.ModelAdmin):
	readonly_fields = ('ballot_paper', 'category_name', 'created_by')
	inlines = [ChoiceInline]
	list_display = ['category_name', 'ballot_paper', 'created_by']


class CategoryInline(admin.TabularInline):
	model = Category


class BallotAdmin(admin.ModelAdmin):
	prepopulated_fields = {'ballot_url': ('ballot_name',)}
	readonly_fields = ('created_by',)
	list_display = ['ballot_name', 'created_by', 'is_custom']


admin.site.register(Category, CategoryAdmin)
admin.site.register(BallotPaper, BallotAdmin)
