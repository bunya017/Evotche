from django.conf.urls import url
from django.contrib.auth.views import login

from . import views



app_name = 'users'
urlpatterns = [
	url(r'^login/$', login, {'template_name': 'users/login.html'}, name='login'),
	url(r'^logout/$', views.logout_view, name='logout'),
	url(r'^signup/$', views.signup, name='signup'),
	url(r'^page/(?P<ballot_url>[-\w]+)/$', views.show_ballot_page, name='show_ballot_page'),
]