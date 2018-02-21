from django.conf.urls import url

from . import views



app_name = 'polls'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^vote/(?P<ballot_url>[-\w]+)$', views.vote, name='vote'),
	url(r'^results/$', views.results, name='results'),
	url(r'^results/(?P<ballot_url>[-\w]+)$', views.ballot_results, name='ballot_results'),
	url(r'^new_category/(?P<ball_id>[0-9]+)/$', views.add_new_caty, 
			name='add_new_caty'),
	url(r'^new_choice/(?P<cat_id>[0-9]+)/$', views.add_new_choice, 
			name='add_new_choice'),
	url(r'^new_ballot/$', views.add_new_ballot, name='add_new_ballot'),
	url(r'^ballot/$', views.ballot, name='ballot'),
	url(r'^ballot/(?P<ball_id>[0-9]+)/$', views.category_view, name='category_view'),
	url(r'^category/(?P<cat_id>[0-9]+)/$', views.choice_view, name='choice_view'),
	url(r'^delete/(?P<ball_id>[0-9]+)/$', views.delete_ballot, name='delete_ballot'),
	url(r'^delete/category/(?P<cat_id>[0-9]+)/$', views.delete_caty, name='delete_caty'),
	url(r'^delete/choice/(?P<ch_id>[0-9]+)/$', views.delete_choice, name='delete_choice'),

]