from django.conf.urls import patterns, url

import games.views

urlpatterns = patterns('',
		url(r'^(\d+)/(home)/$', games.views.test_view),
		url(r'^(\d+)/(away)/$', games.views.test_view),
	)