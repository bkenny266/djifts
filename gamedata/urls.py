from django.conf.urls import patterns, include, url
from gamedata import views

urlpatterns = patterns('',
		url(r'^database/$', views.show_games),

	)
