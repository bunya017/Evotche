from django.conf.urls import include, url
from . import views



app_name = 'trxns'
urlpatterns = [
	url(r'^pay/(?P<ref_code>[0-9a-zA-Z ]+)/$', views.pay, name='pay'),
	url(r'^buy-tokens/(?P<ballot_url>[-\w]+)/$', views.buy_tokens, name='buy_tokens'),
]