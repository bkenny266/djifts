from django.conf.urls import patterns, url

from teams import views

urlpatterns = patterns('',
	url(r'^$', views.team_list), 
    url(r'^(\d{1,2})/$', views.get_team_page),
)